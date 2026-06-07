const $ = (id) => document.getElementById(id);
const ACCENT = "#e781fd";
const ACCENT_FILL = "rgba(231, 129, 253, 0.1)";

let locale = localStorage.getItem("serenity-locale") || (navigator.language.startsWith("zh") ? "zh" : "en");
let i18n = {};
let chartInstances = [];
let sessionId = localStorage.getItem("serenity-session-id") || null;
let abortController = null;
let sessionsSupported = false;
let streamSupported = false;
let deepseekAvailable = false;
let agentPlanState = null;
let fakeProgressTimer = null;
let activeAssistantBody = null;
let chatInFlight = false;

const STEPS_BY_MODE = {
  A: ["route", "corpus", "live_web", "stale", "render", "llm"],
  B: ["route", "radar", "live_web", "stale", "render", "llm"],
  C: ["route", "corpus", "live_web", "stale", "render", "llm"],
  D: ["route", "corpus", "live_web", "stale", "render", "llm"],
  E: ["route", "corpus", "render", "llm"],
  brief: ["route", "brief", "render", "llm"],
};

const STEP_LABELS = {
  route: { en: "Route query & detect mode", zh: "识别查询与模式" },
  corpus: { en: "Load Serenity corpus", zh: "加载 Serenity 语料" },
  lookup: { en: "Load Serenity corpus", zh: "加载 Serenity 语料" },
  live_web: { en: "Fetch live market data", zh: "获取实时行情与新闻" },
  radar: { en: "Compute attention radar", zh: "计算注意力 Radar" },
  stale: { en: "Check thesis freshness", zh: "检查 thesis 时效" },
  brief: { en: "Load daily brief", zh: "读取 daily brief" },
  render: { en: "Build structured report", zh: "生成结构化报告" },
  llm: { en: "Agent narrative synthesis", zh: "Agent 叙述合成" },
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const ctype = res.headers.get("content-type") || "";
  const raw = await res.text();
  if (!ctype.includes("application/json")) {
    if (raw.trimStart().startsWith("<")) {
      throw new Error(
        "Server returned HTML instead of JSON. Restart the UI server: python aio_serenity.py"
      );
    }
    throw new Error(raw.slice(0, 200) || res.statusText);
  }
  let data;
  try {
    data = JSON.parse(raw);
  } catch (_) {
    throw new Error("Invalid JSON from server. Restart: python aio_serenity.py");
  }
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function t(key) {
  return (i18n[locale] && i18n[locale][key]) || key;
}

function detectPromptLocale(prompt) {
  if (/[\u4e00-\u9fff]/.test(prompt)) return "zh";
  if (/[A-Za-z]{3,}/.test(prompt)) return "en";
  return locale;
}

function formatAgentMarkdown(text) {
  if (!text) return "";
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (s) =>
    esc(s)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let inUl = false;
  const closeUl = () => {
    if (inUl) {
      out.push("</ul>");
      inUl = false;
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      closeUl();
      continue;
    }
    if (line.startsWith("### ")) {
      closeUl();
      out.push(`<h4>${inline(line.slice(4))}</h4>`);
    } else if (line.startsWith("## ")) {
      closeUl();
      out.push(`<h3>${inline(line.slice(3))}</h3>`);
    } else if (line.startsWith("# ")) {
      closeUl();
      out.push(`<h3>${inline(line.slice(2))}</h3>`);
    } else if (/^[-*]\s+/.test(line)) {
      if (!inUl) {
        out.push('<ul class="agent-md-list">');
        inUl = true;
      }
      out.push(`<li>${inline(line.replace(/^[-*]\s+/, ""))}</li>`);
    } else {
      closeUl();
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  closeUl();
  return out.join("");
}

function guessMode(prompt) {
  const p = prompt.toLowerCase();
  if (p.includes("daily brief") || p.includes("daily-brief")) return "brief";
  if (p.includes("radar") || p.includes("heating") || p.includes("注意力")) return "B";
  if (p.includes("研报") || p.includes("thesis memo")) return "D";
  if (p.includes("产业链") || p.includes("theme scan") || p.includes("etf")) return "C";
  if (
    p.includes("fresh-name") ||
    p.includes("fresh name") ||
    p.includes("never covered") ||
    p.includes("methodology checklist")
  ) {
    return "A";
  }
  if (
    p.includes("teach me") ||
    p.includes("one question at a time") ||
    p.includes("learn her research") ||
    p.includes("带我学")
  ) {
    return "E";
  }
  return "A";
}

function hideEmptyState() {
  const empty = $("empty-state");
  const msgs = $("chat-messages");
  if (empty) empty.classList.add("hidden");
  if (msgs) msgs.classList.remove("hidden");
}

function showEmptyState() {
  const empty = $("empty-state");
  const msgs = $("chat-messages");
  if (empty) empty.classList.remove("hidden");
  if (msgs) {
    msgs.classList.add("hidden");
    msgs.innerHTML = "";
  }
  activeAssistantBody = null;
}

function appendChatTurn(userPrompt) {
  hideEmptyState();
  const msgs = $("chat-messages");
  const turn = document.createElement("div");
  turn.className = "chat-turn";
  turn.innerHTML = `
    <div class="msg-user"><div class="msg-bubble">${escapeHtml(userPrompt)}</div></div>
    <div class="msg-assistant">
      <img src="/assets/serenity.png" alt="" class="msg-assistant-avatar" width="28" height="28" />
      <div class="msg-assistant-body"></div>
    </div>`;
  msgs.appendChild(turn);
  activeAssistantBody = turn.querySelector(".msg-assistant-body");
  scrollChatToBottom({ force: true });
  return activeAssistantBody;
}

function normalizeStep(step) {
  return step === "lookup" ? "corpus" : step;
}

async function loadI18n() {
  i18n = await api("/i18n.json");
  applyStaticI18n();
}

function applyStaticI18n() {
  $("txt-brand").textContent = t("brand");
  $("txt-tagline").textContent = t("tagline");
  $("txt-prompts").textContent = t("samplePrompts");
  $("txt-tools").textContent = t("quickTools");
  $("txt-history").textContent = t("history");
  $("txt-community").textContent = t("community");
  $("btn-new-chat").textContent = t("newChat");
  $("btn-lookup").textContent = t("lookup");
  $("btn-radar").textContent = t("radar");
  $("btn-brief").textContent = t("dailyBrief");
  $("btn-cancel").textContent = t("cancel");
  $("btn-menu").setAttribute("aria-label", t("menu"));
  $("prompt-input").placeholder = t("placeholder");
  $("txt-run").textContent = t("run");
  $("txt-empty").textContent = t("pickPrompt");
  const banner = $("txt-disclaimer-banner");
  if (banner) banner.textContent = t("disclaimerBanner");
  const sideDisc = $("txt-sidebar-disclaimer");
  if (sideDisc) sideDisc.textContent = t("disclaimerBanner");
  $("txt-footer").textContent = t("footer");
  $("btn-lang").textContent = t("lang");
  updateAgentSynthHint();
  document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
}

function updateAgentSynthHint() {
  const el = $("agent-synth-hint");
  if (!el) return;
  el.textContent = deepseekAvailable ? t("agentSynthOn") : t("agentSynthOff");
  el.className = "agent-synth-hint" + (deepseekAvailable ? " is-on" : "");
}

function updateEnvSetup(status) {
  const panel = $("env-setup");
  if (!panel) return;
  if (deepseekAvailable) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  $("txt-env-title").textContent = t("envTitle");
  $("env-setup-desc").innerHTML = [
    t("envDesc"),
    t("envStep1"),
    t("envStep2"),
    t("envStep3"),
  ].map((s) => `<span class="env-step">${escapeHtml(s)}</span>`).join("<br>");
  $("env-setup-path").textContent = status.env_path || ".env";
  $("env-setup-cursor").textContent = t("envCursorNote");
}

async function loadCommunity() {
  try {
    const data = await api("/api/community");
    $("txt-community").textContent = locale === "zh" ? (data.title_zh || data.title_en) : data.title_en;
    $("community-subtitle").textContent =
      locale === "zh" ? (data.subtitle_zh || data.subtitle_en) : data.subtitle_en;
    const list = $("community-links");
    list.innerHTML = "";
    for (const link of data.links || []) {
      const a = document.createElement("a");
      a.className = "community-link" + (link.dummy ? " is-dummy" : "");
      a.href = link.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      const label = locale === "zh" ? (link.label_zh || link.label_en) : link.label_en;
      a.innerHTML = `<span class="link-icon">${link.icon || "→"}</span><span>${label}</span>`;
      if (link.dummy) a.title = "GitHub URL — coming soon";
      list.appendChild(a);
    }
  } catch (_) {
    $("community-subtitle").textContent = "";
  }
}

function startAgentRun(mode, useLlm) {
  let steps = [...(STEPS_BY_MODE[mode] || STEPS_BY_MODE.A)];
  if (!useLlm) steps = steps.filter((s) => s !== "llm");
  agentPlanState = {
    mode,
    useLlm,
    steps,
    status: Object.fromEntries(steps.map((s) => [s, "pending"])),
    details: {},
    done: false,
  };
  agentPlanState.status[steps[0]] = "active";
  $("composer-inner").classList.add("is-running");
  $("prompt-input").disabled = true;
  renderAgentPlan();
}

function stopAgentRun() {
  stopFakeProgress();
  agentPlanState = null;
  $("composer-inner").classList.remove("is-running");
  if (!chatInFlight) {
    $("prompt-input").disabled = false;
    $("btn-send").disabled = false;
  }
}

function advanceAgentStep(stepId, detail) {
  if (!agentPlanState) return;
  stepId = normalizeStep(stepId);
  const { steps } = agentPlanState;
  const idx = steps.indexOf(stepId);
  if (idx < 0) return;
  for (let i = 0; i < idx; i += 1) agentPlanState.status[steps[i]] = "done";
  agentPlanState.status[stepId] = "active";
  if (detail) agentPlanState.details[stepId] = detail;
  renderAgentPlan();
}

function completeAgentStep(stepId) {
  if (!agentPlanState) return;
  stepId = normalizeStep(stepId);
  const { steps } = agentPlanState;
  if (!steps.includes(stepId)) return;
  agentPlanState.status[stepId] = "done";
  const idx = steps.indexOf(stepId);
  if (idx + 1 < steps.length && agentPlanState.status[steps[idx + 1]] === "pending") {
    agentPlanState.status[steps[idx + 1]] = "active";
  }
  renderAgentPlan();
}

function markAgentPlanDone() {
  if (!agentPlanState) return;
  agentPlanState.steps.forEach((s) => {
    agentPlanState.status[s] = "done";
  });
  agentPlanState.done = true;
  renderAgentPlan(true);
}

function buildAgentPlanHtml(forceDone) {
  if (!agentPlanState) return "";
  const { steps, status, details, done } = agentPlanState;
  const isDone = forceDone || done;
  const headerClass = isDone ? "agent-plan-header is-done" : "agent-plan-header";
  const title = isDone ? t("agentComplete") : t("agentRunning");
  const collapsed = isDone ? " is-collapsed" : "";
  return `
    <div class="agent-plan${collapsed}">
      <div class="${headerClass}">
        <img src="/assets/serenity.png" alt="" class="agent-plan-avatar${isDone ? " is-done" : " is-running"}" width="28" height="28" />
        <span class="agent-plan-title">${title}</span>
        ${isDone ? `<button type="button" class="agent-plan-toggle text-btn" aria-expanded="false">${t("showMore")}</button>` : ""}
      </div>
      <ol class="agent-steps${isDone ? " hidden" : ""}">
        ${steps
          .map((s) => {
            const st = status[s] || "pending";
            const label = (STEP_LABELS[s] && STEP_LABELS[s][locale]) || s;
            const detail = details[s] ? `<span class="step-detail">${escapeHtml(details[s])}</span>` : "";
            return `<li class="agent-step step-${st}"><span class="step-icon"></span><span><span class="step-label">${label}</span>${detail}</span></li>`;
          })
          .join("")}
      </ol>
    </div>`;
}

function renderAgentPlan(forceDone) {
  if (!agentPlanState || !activeAssistantBody) return;
  const html = buildAgentPlanHtml(forceDone);
  const existing = activeAssistantBody.querySelector(".agent-plan");
  if (existing) {
    existing.outerHTML = html;
  } else {
    activeAssistantBody.insertAdjacentHTML("afterbegin", html);
  }
  bindAgentPlanToggle(activeAssistantBody);
  scrollChatToBottom();
}

function bindAgentPlanToggle(container) {
  container.querySelectorAll(".agent-plan-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const plan = btn.closest(".agent-plan");
      const steps = plan && plan.querySelector(".agent-steps");
      if (!steps) return;
      const hidden = steps.classList.toggle("hidden");
      btn.textContent = hidden ? t("showMore") : t("showLess");
      btn.setAttribute("aria-expanded", hidden ? "false" : "true");
    });
  });
}

const SCROLL_STICKY_PX = 100;

function isNearChatBottom() {
  const el = $("output");
  if (!el) return true;
  return el.scrollHeight - el.scrollTop - el.clientHeight <= SCROLL_STICKY_PX;
}

function scrollChatToBottom({ force = false } = {}) {
  const el = $("output");
  if (!el) return;
  if (force || isNearChatBottom()) {
    el.scrollTop = el.scrollHeight;
  }
}

function fillTemplate(text) {
  $("prompt-input").value = text;
  $("prompt-input").focus();
  closeSidebar();
}

function startFakeProgress(mode, useLlm) {
  stopFakeProgress();
  startAgentRun(mode, useLlm);
  const { steps } = agentPlanState;
  let idx = 0;
  fakeProgressTimer = setInterval(() => {
    if (!agentPlanState || idx >= steps.length - 1) {
      stopFakeProgress();
      return;
    }
    completeAgentStep(steps[idx]);
    idx += 1;
  }, 400);
}

function stopFakeProgress() {
  if (fakeProgressTimer) {
    clearInterval(fakeProgressTimer);
    fakeProgressTimer = null;
  }
}

function destroyCharts() {
  chartInstances.forEach((c) => c.destroy());
  chartInstances = [];
}

function renderCharts(container) {
  if (typeof Chart === "undefined") return;
  const isMobile = window.innerWidth < 900;
  container.querySelectorAll("canvas.price-chart").forEach((canvas) => {
    let labels = [];
    let values = [];
    try {
      labels = JSON.parse(canvas.getAttribute("data-labels") || "[]");
      values = JSON.parse(canvas.getAttribute("data-values") || "[]");
    } catch (_) {
      return;
    }
    if (!values.length) return;
    const ctx = canvas.getContext("2d");
    const chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: ACCENT,
          backgroundColor: ACCENT_FILL,
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { maxTicksLimit: isMobile ? 4 : 6, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 10 } }, grid: { color: "#f0f0f0" } },
        },
      },
    });
    chartInstances.push(chart);
  });
}

function bindEvidenceToggles(container) {
  container.querySelectorAll(".toggle-evidence").forEach((btn) => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".thesis-card");
      const list = card && card.querySelector(".thesis-timeline");
      const preview = card && card.querySelector(".thesis-card-preview");
      if (!list) return;
      const hidden = list.classList.toggle("hidden");
      if (preview) preview.classList.toggle("hidden", !hidden);
      btn.textContent = hidden ? btn.dataset.show : btn.dataset.hide;
    });
  });
}

function bindThesisToggles(container) {
  container.querySelectorAll(".toggle-thesis").forEach((btn) => {
    btn.addEventListener("click", () => {
      const full = btn.nextElementSibling;
      if (!full) return;
      if (window.innerWidth < 900) {
        $("modal-body").innerHTML = full.innerHTML;
        $("thesis-modal").classList.remove("hidden");
        return;
      }
      const hidden = full.classList.toggle("hidden");
      btn.textContent = hidden ? btn.dataset.show : btn.dataset.hide;
    });
  });
}

function mountReportInAssistant(html, { replace = false } = {}) {
  const target = activeAssistantBody;
  if (!target) return null;
  let shell = target.querySelector(".report-shell");
  if (replace || !shell) {
    destroyCharts();
    if (replace) {
      const planHtml = target.querySelector(".agent-plan")?.outerHTML || "";
      target.innerHTML = planHtml + `<div class="report-shell report-fade-in">${html}</div>`;
    } else if (!shell) {
      target.insertAdjacentHTML("beforeend", `<div class="report-shell report-fade-in">${html}</div>`);
    } else {
      shell.innerHTML = html;
      shell.classList.add("report-fade-in");
    }
    shell = target.querySelector(".report-shell");
  } else {
    shell.innerHTML = html;
    shell.classList.add("report-fade-in");
  }
  if (shell) {
    renderCharts(shell);
    bindThesisToggles(shell);
    bindEvidenceToggles(shell);
    bindAgentPlanToggle(target);
  }
  scrollChatToBottom();
  return shell ? shell.querySelector(".agent-narrative, .llm-narrative") : null;
}

function setAssistantHtml(html) {
  return mountReportInAssistant(html, { replace: true });
}

function setOutputHtml(html, meta = "") {
  if (activeAssistantBody) {
    setAssistantHtml(html);
  } else if (!html) {
    showEmptyState();
  }
  $("meta").textContent = meta;
}

async function ensureSession() {
  if (!sessionsSupported) return null;
  if (sessionId) return sessionId;
  try {
    const sess = await api("/api/sessions", { method: "POST", body: "{}" });
    sessionId = sess.id;
    localStorage.setItem("serenity-session-id", sessionId);
    await loadSessions();
    return sessionId;
  } catch (_) {
    sessionsSupported = false;
    return null;
  }
}

async function loadSessions() {
  if (!sessionsSupported) return;
  try {
    const { sessions } = await api("/api/sessions");
    const list = $("session-list");
    list.innerHTML = "";
    for (const s of sessions) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "session-item" + (s.id === sessionId ? " active" : "");
      btn.textContent = s.title || "Chat";
      btn.title = s.title;
      btn.addEventListener("click", () => loadSession(s.id));
      list.appendChild(btn);
    }
  } catch (_) {
    sessionsSupported = false;
  }
}

async function loadSession(id) {
  sessionId = id;
  localStorage.setItem("serenity-session-id", sessionId);
  await loadSessions();
  const { messages } = await api(`/api/sessions/${id}`);
  if (!messages.length) {
    showEmptyState();
    return;
  }
  $("chat-messages").innerHTML = "";
  for (const msg of messages) {
    appendChatTurn(msg.prompt || "");
    let html = msg.html_snapshot || "";
    if (msg.llm_narrative && html.includes("llm-narrative")) {
      html = html.replace(
        '<div class="llm-narrative agent-narrative"></div>',
        `<div class="llm-narrative agent-narrative">${formatAgentMarkdown(msg.llm_narrative)}</div>`
      );
      html = html.replace("llm-narrative-section hidden", "llm-narrative-section");
    }
    setAssistantHtml(html);
    bindAgentPlanToggle($("chat-messages"));
  }
  const last = messages[messages.length - 1];
  $("meta").textContent = last.prompt?.slice(0, 80) || "";
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function loadStatus() {
  try {
    const s = await api("/api/status");
    const ver = String(s.ui_version || "0.1.0");
    sessionsSupported = ver >= "0.3.0";
    streamSupported = ver >= "0.3.0";
    deepseekAvailable = !!s.deepseek_available;
    const pills = [
      `<span class="pill ok">${t("corpus")}: ${s.corpus_tweets} ${t("tweets")}</span>`,
      `<span class="pill ${s.live_web_available ? "ok" : "warn"}">${t("liveWeb")}: ${s.live_web_available ? "✓" : "✗"}</span>`,
      `<span class="pill ${deepseekAvailable ? "ok" : ""}">${t("deepseek")}: ${deepseekAvailable ? "✓" : "✗"}</span>`,
    ];
    if (s.agent_parity) pills.push('<span class="pill ok">Agent path</span>');
    if (!streamSupported) pills.push(`<span class="pill warn">${t("restartServer")}</span>`);
    $("status-bar").innerHTML = pills.join("");
    updateAgentSynthHint();
    updateEnvSetup(s);
  } catch (_) {
    $("status-bar").innerHTML = `<span class="pill warn">${t("offline")}</span>`;
  }
}

async function loadPrompts() {
  const { prompts } = await api("/api/prompts");
  const list = $("prompt-list");
  list.innerHTML = "";
  for (const p of prompts) {
    const title = locale === "zh"
      ? (p.title_zh || p.label_zh || p.label)
      : (p.title_en || p.label_en || p.label);
    const subtitle = locale === "zh"
      ? (p.subtitle_zh || p.subtitle_en || "")
      : (p.subtitle_en || p.subtitle_zh || "");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "prompt-btn";
    btn.innerHTML = `<span class="prompt-title">${escapeHtml(title)}</span>${subtitle ? `<span class="prompt-sub">${escapeHtml(subtitle)}</span>` : ""}`;
    btn.addEventListener("click", () => {
      const prompt = locale === "zh" ? (p.prompt_zh || p.prompt) : (p.prompt_en || p.prompt);
      fillTemplate(prompt);
    });
    list.appendChild(btn);
  }
}

function formatMeta(result) {
  const parts = [
    `${t("mode")} ${result.mode}`,
    result.ticker ? `$${result.ticker}` : null,
    `${t("liveWebAuto")}: ${result.live_web_used ? t("yes") : t("no")}`,
    `${t("llm")}: ${result.llm_used ? t("yes") : t("no")}`,
  ];
  if (result.locale_issues && result.locale_issues.length) {
    parts.push(`⚠ ${result.locale_issues[0]}`);
  }
  return parts.filter(Boolean).join(" · ");
}

function handleProgress(payload) {
  const step = normalizeStep(payload.step || "");
  const msg = payload.message || "";
  if (step === "route" && msg.match(/Mode\s(\w+)/i)) {
    const detected = msg.match(/Mode\s(\w+)/i)[1];
    if (!agentPlanState || agentPlanState.mode !== detected) {
      startAgentRun(detected, deepseekAvailable);
    }
  }
  if (step) advanceAgentStep(step, msg);
}

function finalizeChatTurn(meta) {
  if (agentPlanState) {
    markAgentPlanDone();
    renderAgentPlan(true);
  }
  stopFakeProgress();
  stopAgentRun();
  chatInFlight = false;
  $("btn-send").disabled = false;
  $("btn-cancel").classList.add("hidden");
  $("prompt-input").disabled = false;
  if (meta) $("meta").textContent = meta;
}

function showReport(html, meta, { streaming = false } = {}) {
  stopFakeProgress();
  const narrativeEl = mountReportInAssistant(html, { replace: !streaming });
  if (!streaming) {
    finalizeChatTurn(meta);
  } else if (meta) {
    $("meta").textContent = meta;
  }
  return narrativeEl;
}

async function runChatViaJson(body, modeGuess) {
  startFakeProgress(modeGuess, deepseekAvailable);
  try {
    const result = await api("/api/chat", { method: "POST", body: JSON.stringify(body) });
    showReport(result.html, formatMeta(result), { streaming: false });
    return result;
  } finally {
    stopFakeProgress();
  }
}

async function runChatStream(body, modeGuess) {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: abortController.signal,
  });

  const ctype = res.headers.get("content-type") || "";
  if (res.status === 404 || ctype.includes("text/html")) {
    return runChatViaJson(body, modeGuess);
  }
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText.slice(0, 300) || res.statusText);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult = null;
  let narrativeEl = null;
  let llmStarted = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const block of parts) {
      const lines = block.split("\n");
      let event = "message";
      let dataLine = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) dataLine = line.slice(5).trim();
      }
      if (!dataLine) continue;
      let payload;
      try {
        payload = JSON.parse(dataLine);
      } catch (_) {
        continue;
      }

      if (event === "progress") {
        handleProgress(payload);
      } else if (event === "result") {
        finalResult = payload.data;
        completeAgentStep("render");
        narrativeEl = showReport(finalResult.html, formatMeta(finalResult), { streaming: true });
        if (narrativeEl) {
          const section = narrativeEl.closest(".llm-narrative-section");
          if (section) section.classList.remove("hidden");
          narrativeEl.innerHTML = "";
          narrativeEl.dataset.raw = "";
        }
        if (!deepseekAvailable || !finalResult.deepseek_available) {
          finalizeChatTurn(formatMeta(finalResult));
        }
      } else if (event === "token" && narrativeEl) {
        if (!llmStarted) {
          advanceAgentStep("llm", t("agentAnswer") || t("agentAnalysis"));
          llmStarted = true;
        }
        narrativeEl.dataset.raw = (narrativeEl.dataset.raw || "") + (payload.text || "");
        narrativeEl.innerHTML = formatAgentMarkdown(narrativeEl.dataset.raw);
        scrollChatToBottom();
      } else if (event === "done") {
        finalResult = payload.data || finalResult;
        if (narrativeEl && narrativeEl.dataset.raw) {
          narrativeEl.innerHTML = formatAgentMarkdown(narrativeEl.dataset.raw);
        }
        if (llmStarted) completeAgentStep("llm");
        finalizeChatTurn(finalResult ? formatMeta(finalResult) : "");
      } else if (event === "saved") {
        loadSessions();
      } else if (event === "error") {
        throw new Error(payload.message || "Stream error");
      }
    }
  }

  if (!finalResult) {
    return runChatViaJson(body, modeGuess);
  }
  return finalResult;
}

async function runChat(forcedMode) {
  const prompt = $("prompt-input").value.trim();
  if (!prompt || chatInFlight) return;

  const modeGuess = forcedMode || guessMode(prompt);
  $("prompt-input").value = "";
  appendChatTurn(prompt);
  startAgentRun(modeGuess, deepseekAvailable);
  chatInFlight = true;

  abortController = new AbortController();
  $("btn-send").disabled = true;
  $("prompt-input").disabled = true;
  $("btn-cancel").classList.remove("hidden");

  try {
    await ensureSession();
    const body = { prompt, locale: detectPromptLocale(prompt) };
    if (sessionId) body.session_id = sessionId;
    if (forcedMode) body.mode = forcedMode;

    if (streamSupported) {
      await runChatStream(body, modeGuess);
    } else {
      await runChatViaJson(body, modeGuess);
    }
  } catch (e) {
    chatInFlight = false;
    stopAgentRun();
    $("btn-send").disabled = false;
    $("prompt-input").disabled = false;
    $("btn-cancel").classList.add("hidden");
    if (e.name !== "AbortError") {
      mountReportInAssistant(`<div class="alert alert-warning"><strong>Error</strong><p>${escapeHtml(e.message)}</p></div>`, { replace: false });
    } else if (activeAssistantBody) {
      const shell = activeAssistantBody.querySelector(".report-shell");
      const cancelHtml = `<p class="synthesis-note">${t("cancel")}</p>`;
      if (shell) shell.innerHTML = cancelHtml;
      else activeAssistantBody.insertAdjacentHTML("beforeend", `<div class="report-shell">${cancelHtml}</div>`);
    }
  } finally {
    abortController = null;
  }
}

function cancelChat() {
  if (abortController) abortController.abort();
  chatInFlight = false;
  stopAgentRun();
  $("btn-send").disabled = false;
  $("prompt-input").disabled = false;
  $("btn-cancel").classList.add("hidden");
}

async function newChat() {
  sessionId = null;
  localStorage.removeItem("serenity-session-id");
  $("prompt-input").value = "";
  showEmptyState();
  $("meta").textContent = "";
  try {
    await ensureSession();
  } catch (_) {
    /* optional */
  }
}

function openSidebar() {
  $("sidebar").classList.add("open");
  $("sidebar-backdrop").classList.remove("hidden");
}

function closeSidebar() {
  $("sidebar").classList.remove("open");
  $("sidebar-backdrop").classList.add("hidden");
}

async function quickLookup() {
  const ticker = $("ticker-input").value.trim().toUpperCase().replace("$", "");
  if (!ticker) return;
  fillTemplate(locale === "zh"
    ? `Serenity 怎么看 $${ticker}？`
    : `What is Serenity's view on $${ticker}?`);
}

async function quickRadar() {
  fillTemplate(locale === "zh"
    ? "用 serenity-twin：跑 radar（14 天）"
    : "Run Serenity radar 14d window");
}

async function quickBrief() {
  fillTemplate(locale === "zh"
    ? "用 serenity-twin：读 daily-brief-latest.txt 并总结"
    : "Summarize daily brief Heating tickers and corpus views.");
}

$("btn-send").addEventListener("click", () => runChat());
$("btn-cancel").addEventListener("click", cancelChat);
$("btn-new-chat").addEventListener("click", newChat);
$("btn-lookup").addEventListener("click", quickLookup);
$("btn-radar").addEventListener("click", quickRadar);
$("btn-brief").addEventListener("click", quickBrief);
$("btn-menu").addEventListener("click", openSidebar);
$("sidebar-backdrop").addEventListener("click", closeSidebar);
$("modal-close").addEventListener("click", () => $("thesis-modal").classList.add("hidden"));
$("thesis-modal").querySelector(".modal-backdrop").addEventListener("click", () => $("thesis-modal").classList.add("hidden"));

$("btn-lang").addEventListener("click", () => {
  locale = locale === "zh" ? "en" : "zh";
  localStorage.setItem("serenity-locale", locale);
  loadI18n().then(() => {
    loadPrompts();
    loadStatus();
    loadCommunity();
  });
});

$("prompt-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    runChat();
  }
});

function showBootError(err) {
  const shell = document.querySelector(".app-shell");
  if (shell) {
    shell.innerHTML = `<div class="boot-error"><strong>${escapeHtml(t("bootError"))}</strong><p>${escapeHtml(err.message || String(err))}</p></div>`;
  }
}

(async () => {
  try {
    await loadI18n();
    await loadStatus();
    await loadPrompts();
    await loadCommunity();
    try {
      await ensureSession();
    } catch (_) {
      /* optional */
    }
  } catch (e) {
    showBootError(e);
  }
})();
