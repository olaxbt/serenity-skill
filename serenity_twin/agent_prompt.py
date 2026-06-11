"""Load SKILL + workflow excerpts for browser UI agent (Cursor-parity prompts)."""

from __future__ import annotations

from serenity_twin.paths import REASONING, ROOT

SKILL = ROOT / "SKILL.md"
MAX_WORKFLOW_CHARS = 6000


def _read(path, limit: int = MAX_WORKFLOW_CHARS) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")[:limit]


_FORMAT_RULES = {
    "en": (
        "OUTPUT FORMAT (strict — professional research memo style):\n"
        "1. Open with ## Executive summary — 2–3 sentences that answer the user's question directly. "
        "No preamble ('Certainly', 'Great question', 'I'd be happy to').\n"
        "2. Use only the ## section headers listed for this mode, in order. Omit empty sections.\n"
        "3. Per section: either one short paragraph (max 3 sentences) OR a bullet list (3–6 items with '-'). "
        "Do not stack long prose and long lists in the same section.\n"
        "4. Blank line between sections. Use ### only for sub-layers (e.g. individual scarce layers in Mode C).\n"
        "5. Tag evidence source inline: *corpus*, *live verification*, *research map*.\n"
        "6. Tickers as $TICKER; dates as YYYY-MM-DD when known.\n"
        "7. No emoji. No numbered essay paragraphs (1. 2. 3. as section bodies). "
        "No markdown tables — use bullets."
    ),
    "zh": (
        "输出格式（严格 — 专业研报风格）：\n"
        "1. 以 ## 执行摘要 开头 — 2–3 句直接回答用户问题，不要套话。\n"
        "2. 仅使用本模式列出的 ## 小节标题，按顺序；无内容则跳过。\n"
        "3. 每个小节：一段短文字（最多 3 句）或 3–6 条 '-' 列表，不要混用长段+长列表。\n"
        "4. 小节之间空一行。### 仅用于子层级（如 Mode C 的单个 scarce layer）。\n"
        "5. 证据来源标注：*语料*、*实时核验*、*研究地图*。\n"
        "6. 代码用 $TICKER；日期用 YYYY-MM-DD。\n"
        "7. 不用 emoji；不用编号长文；不用 markdown 表格 — 用列表。"
    ),
}

_MODE_A_SECTIONS = {
    "en": (
        "Mode A — Ticker view. After Executive summary, use these ## headers in order:\n"
        "- Serenity's corpus view\n"
        "- Live verification\n"
        "- Plain-language summary\n"
        "- First-principles check\n"
        "- Buffett-style assessment\n"
        "- Key risks\n"
        "- What would falsify this view"
    ),
    "zh": (
        "Mode A — 单标的观点。执行摘要之后，按顺序使用以下 ## 标题：\n"
        "- 她的观点\n"
        "- Live verification（可保留英文）\n"
        "- 小白解释\n"
        "- 第一性原理\n"
        "- Buffett 直接判断\n"
        "- 主要风险\n"
        "- 什么情况说明判断错了"
    ),
}

_MODE_B_SECTIONS = {
    "en": (
        "Mode B — Attention radar. After Executive summary, use these ## headers in order:\n"
        "- What's heating\n"
        "- New entrants\n"
        "- Conviction watch\n"
        "- Theme rotation\n"
        "- Corpus cross-check\n"
        "- Research priorities"
    ),
    "zh": (
        "Mode B — 注意力雷达。执行摘要之后，按顺序使用：\n"
        "- 升温标的\n"
        "- 新进标的\n"
        "- 信念观察\n"
        "- 主题轮动\n"
        "- 语料交叉验证\n"
        "- 后续研究优先级"
    ),
}

_MODE_C_SECTIONS = {
    "en": (
        "Mode C — Theme / supply-chain scan. After Executive summary, use these ## headers in order:\n"
        "- System change & demand driver\n"
        "- Value-chain layer ranking\n"
        "- Scarce layers (ranked)\n"
        "- Research candidates\n"
        "- Serenity corpus cross-check\n"
        "- ETF / passive fit (only if user asked for ETF or fund exposure)\n"
        "- Key risks & falsifiers\n"
        "- Next verification steps\n"
        "Rank layers before companies. Do not default to a single-stock chart narrative."
    ),
    "zh": (
        "Mode C — 产业链 / 主题扫描。执行摘要之后，按顺序使用：\n"
        "- 系统变化与需求驱动\n"
        "- 产业链层级排序\n"
        "- 稀缺层（排序）\n"
        "- 研究候选标的\n"
        "- Serenity 语料交叉验证\n"
        "- ETF / 被动配置（仅当用户明确询问 ETF 或基金）\n"
        "- 主要风险与证伪条件\n"
        "- 下一步核验\n"
        "先排层级再排个股；不要写成单股走势图叙述。"
    ),
}

_MODE_D_SECTIONS = {
    "en": (
        "Mode D — Research memo. After Executive summary, use these ## headers in order:\n"
        "- System change\n"
        "- Value chain & scarce layers\n"
        "- Serenity corpus view\n"
        "- Live verification\n"
        "- Evidence ladder\n"
        "- Financial & moat check\n"
        "- Key risks & falsifiers\n"
        "- Conclusion tier"
    ),
    "zh": (
        "Mode D — 深度研报。执行摘要之后，按顺序使用：\n"
        "- 系统变化\n"
        "- 产业链与稀缺层\n"
        "- Serenity 语料观点\n"
        "- 实时核验\n"
        "- 证据阶梯\n"
        "- 财务与护城河\n"
        "- 主要风险与证伪条件\n"
        "- 结论 tier"
    ),
}

_MODE_E_SECTIONS = {
    "en": (
        "Mode E — Method coaching. Use exactly ONE ## header this turn:\n"
        "- This turn's question\n"
        "Under it: 2–3 sentences of context, then ONE focused question for the user. "
        "No stock picks. No multi-section dump."
    ),
    "zh": (
        "Mode E — 方法辅导。本轮仅使用一个 ## 标题：\n"
        "- 本轮问题\n"
        "其下：2–3 句背景，然后向用户提出一个聚焦问题。不荐股，不多节堆砌。"
    ),
}

_MODE_BRIEF_SECTIONS = {
    "en": (
        "Daily brief. After Executive summary, use:\n"
        "- Heating snapshot\n"
        "- Corpus cross-check\n"
        "- What to watch today"
    ),
    "zh": (
        "Daily brief。执行摘要之后使用：\n"
        "- 升温快照\n"
        "- 语料对照\n"
        "- 今日关注"
    ),
}

_MODE_SECTIONS = {
    "A": _MODE_A_SECTIONS,
    "B": _MODE_B_SECTIONS,
    "C": _MODE_C_SECTIONS,
    "D": _MODE_D_SECTIONS,
    "E": _MODE_E_SECTIONS,
    "brief": _MODE_BRIEF_SECTIONS,
}


def build_agent_system_prompt(mode: str, *, locale: str = "en") -> str:
    """System prompt mirroring Cursor Agent + SKILL.md for the given mode."""
    loc = locale if locale in ("en", "zh") else "en"
    exec_header = "Executive summary" if loc == "en" else "执行摘要"
    lang_rule = (
        "LANGUAGE (strict): Write the ENTIRE answer — every heading and sentence — in English. "
        f"Use '{exec_header}' as the first ## header, then only the English section headers listed below — "
        "never Chinese headings from SKILL.md. Ticker symbols and proper nouns may stay as-is."
        if loc == "en"
        else f"LANGUAGE (strict): 全文使用中文。第一个 ## 标题为「{exec_header}」，其余按下列中文标题。"
    )
    base = (
        "You are Serenity Twin — the same research agent as the Cursor SKILL, running in the browser UI. "
        "Scripts have ALREADY executed: lookup_ticker, live_research (quote/news/SEC), stale_check, radar if needed. "
        "Your job: write the PRIMARY research answer that directly addresses the user's question. "
        "This is the main deliverable — lead with the answer, not process narration. "
        "Rules: reconcile corpus vs live_web; respect stale flags; use evidence-ladder grading; "
        "clearly label Serenity corpus view vs independent verification vs research map; no buy/sell orders. "
        f"{lang_rule}\n\n{_FORMAT_RULES[loc]}"
        + (
            "\nEnd with one line: Research support only. Not investment advice."
            if loc == "en"
            else "\n结尾一行：仅作信息跟踪，不构成投资建议。"
        )
    )
    extras: list[str] = []
    mode_sections = _MODE_SECTIONS.get(mode)
    if mode_sections:
        extras.append(mode_sections[loc])
    if mode == "C":
        wf = _read(REASONING / "references" / "deep-research-workflow.md", 3500)
        if wf:
            extras.append(f"Workflow reference:\n{wf}")
    if mode == "D":
        tpl = _read(REASONING / "assets" / "thesis-template.md", 2500)
        if tpl:
            extras.append(f"Memo skeleton reference:\n{tpl}")
    skill_excerpt = _read(SKILL, 4000)
    locale_note = (
        "Note: SKILL excerpt may show 中文 section names — ignore those; use the English headers above."
        if loc == "en"
        else ""
    )
    parts = [base, *extras]
    if locale_note:
        parts.append(locale_note)
    parts.append(f"SKILL excerpt:\n{skill_excerpt}")
    return "\n\n".join(parts)
