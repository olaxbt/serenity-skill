"""Mode routing and optional DeepSeek chat for the browser UI."""

from __future__ import annotations

import html
import importlib.util
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from serenity_twin.llm import load_deepseek_key
from serenity_twin.paths import DATA, MENTIONS_EVENTS_CSV, ROOT
from serenity_twin.report import format_ticker_report
from serenity_twin.web_research import (
    format_live_web_markdown,
    research_radar_tickers,
    research_theme,
    research_ticker,
)

TICKER_DOLLAR = re.compile(r"\$([A-Z]{1,5})\b")
TICKER_ISOLATED = re.compile(r"(?<![A-Z\$])([A-Z]{2,5})(?![A-Z])")
STOPWORDS = frozenset(
    {
        "SERENITY",
        "TWIN",
        "MODE",
        "THE",
        "AND",
        "FOR",
        "WITH",
        "FROM",
        "WHAT",
        "VIEW",
        "RUN",
        "API",
        "ETF",
        "HK",
        "US",
    }
)


def extract_ticker(text: str) -> str | None:
    upper = text.upper()
    m = TICKER_DOLLAR.search(upper)
    if m:
        return m.group(1)
    for m in TICKER_ISOLATED.finditer(upper):
        t = m.group(1)
        if t not in STOPWORDS:
            return t
    return None


def _import_script_module(name: str, rel_path: str) -> Any:
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def detect_prompt_locale(prompt: str, ui_locale: str = "en") -> str:
    """Answer in the language the user wrote — not the UI chrome locale."""
    if re.search(r"[\u4e00-\u9fff]", prompt):
        return "zh"
    if re.search(r"[A-Za-z]{3,}", prompt):
        return "en"
    return ui_locale if ui_locale in ("en", "zh") else "en"


def detect_mode(prompt: str) -> str:
    p = prompt.lower()
    if any(k in p for k in ("daily brief", "daily-brief", "daily-brief-latest")):
        return "brief"
    if any(k in p for k in ("radar", "ramp", "heating", "注意力", "主题轮动")):
        return "B"
    if any(k in p for k in ("深度研报", "thesis memo", "thesis-template", "研报")):
        return "D"
    if any(k in p for k in ("深度调研", "产业链", "a股", "a-share", "theme scan", "etf", "基金", "scorecard")):
        return "C"
    if any(
        k in p
        for k in (
            "fresh-name",
            "fresh name",
            "never covered",
            "methodology checklist",
            "not in corpus",
            "未覆盖",
            "未深度覆盖",
        )
    ):
        return "A"
    if any(
        k in p
        for k in (
            "teach me",
            "带我学",
            "one question at a time",
            "learn her research",
            "learn serenity-style",
            "学 serenity",
            "对话式",
            "method coaching",
        )
    ):
        return "E"
    if any(k in p for k in ("daily brief", "daily-brief")):
        return "brief"
    return "A"


def run_lookup(ticker: str) -> dict:
    mod = _import_script_module("lookup_ticker", "scripts/lookup_ticker.py")
    return mod.lookup(ticker)


def run_radar(window: int = 14, top: int = 12) -> tuple[dict, str]:
    from serenity_twin.csv_util import read_csv

    radar_mod = _import_script_module("radar", "scripts/radar.py")
    if not MENTIONS_EVENTS_CSV.exists():
        raise FileNotFoundError("mentions-events.csv missing — run init_system.py")
    events = read_csv(MENTIONS_EVENTS_CSV)
    dates = sorted({(e.get("created_at") or "")[:10] for e in events if e.get("created_at")})
    asof = dates[-1] if dates else date.today().isoformat()
    result = radar_mod.compute_radar(events, asof, window, top)
    return result, radar_mod.format_text(result)


def enrich_live_web(ctx: dict[str, Any], mode: str, prompt: str) -> None:
    """Always fetch live data for analysis modes — no user must say 'search internet'."""
    if mode in ("E", "brief"):
        return
    try:
        if mode == "B" and ctx.get("radar"):
            heating = [r["ticker"] for r in ctx["radar"].get("heating", [])[:3]]
            if heating:
                ctx["live_web"] = research_radar_tickers(heating)
        elif ctx.get("ticker"):
            ctx["live_web"] = research_ticker(ctx["ticker"])
        elif mode in ("C", "D"):
            ctx["live_web"] = research_theme(prompt)
        elif mode == "A":
            t = extract_ticker(prompt)
            if t:
                ctx["ticker"] = t
                ctx["lookup"] = run_lookup(t)
                ctx["live_web"] = research_ticker(t)
    except Exception as exc:
        ctx["live_web"] = {"status": "error", "error": str(exc)}


def build_context(mode: str, prompt: str, ticker: str | None) -> dict[str, Any]:
    ctx: dict[str, Any] = {"mode": mode, "prompt": prompt}
    if mode == "A" or (mode in ("C", "D", "E") and ticker):
        t = ticker or extract_ticker(prompt)
        if t:
            ctx["ticker"] = t
            ctx["lookup"] = run_lookup(t)
    if mode == "B":
        data, text = run_radar()
        ctx["radar"] = data
        ctx["radar_text"] = text
    if mode == "brief":
        latest = DATA / "daily-brief-latest.txt"
        ctx["daily_brief"] = latest.read_text(encoding="utf-8") if latest.exists() else None
        try:
            data, text = run_radar()
            ctx["radar"] = data
            ctx["radar_text"] = text
        except Exception:
            pass
    enrich_live_web(ctx, mode, prompt)
    if ctx.get("lookup") and ctx.get("ticker"):
        from serenity_twin.stale_check import assess_stale

        lookup = ctx["lookup"]
        th_md = (lookup.get("thesis") or {}).get("markdown")
        quote = (ctx.get("live_web") or {}).get("quote")
        ctx["stale"] = assess_stale(
            thesis_markdown=th_md,
            quote=quote if isinstance(quote, dict) else None,
            recent_tweets=lookup.get("recent_tweets"),
        )
    return ctx


def deterministic_markdown(mode: str, ctx: dict[str, Any]) -> str:
    parts: list[str] = [f"**Mode {mode}** — corpus scripts + **auto live web** executed", ""]

    if "lookup" in ctx:
        parts.append(format_ticker_report(ctx["lookup"]))
    if ctx.get("live_web"):
        parts.append(format_live_web_markdown(ctx["live_web"]))
    if "radar_text" in ctx:
        parts.append(ctx["radar_text"])

    if ctx.get("live_web") and ctx.get("lookup"):
        lookup = ctx["lookup"]
        if lookup.get("found_in_theses"):
            parts.append(
                "## Corpus vs live\n\n"
                "Compare **Serenity thesis age** with **live quote/news** above. "
                "If thesis latest stance is >60 days old and price/news materially changed, flag ⚠️ **stale — re-verify thesis**."
            )
    if ctx.get("daily_brief"):
        parts.append("## Daily brief\n\n" + ctx["daily_brief"])

    if mode == "C":
        parts.append(
            "## Mode C synthesis\n\n"
            "Layer ranking uses live web sources above + Serenity methodology. "
            "Set `DEEPSEEK_API_KEY` for full LLM narrative, or use Cursor Agent."
        )
    if mode == "D":
        tpl = ROOT / "reasoning" / "assets" / "thesis-template.md"
        if tpl.exists():
            parts.append("## Report skeleton\n\n" + tpl.read_text(encoding="utf-8")[:4000])
    if mode == "E":
        parts.append("## Mode E — Learning\n\nLive web skipped for tutoring mode.")

    parts.append("\n---\n*Research support only. Not investment advice.*")
    return "\n\n".join(parts)


def chat_completion(prompt: str, context: dict[str, Any], *, api_key: str | None = None) -> str | None:
    from serenity_twin.llm_stream import chat_completion_sync

    api_key = api_key or load_deepseek_key()
    if not api_key:
        return None
    mode = context.get("mode", "A")
    try:
        out = chat_completion_sync(prompt, context, api_key=api_key)
        return out.strip() if out else None
    except Exception as exc:
        return f"LLM error: {exc}\n\nFalling back to deterministic output below.\n\n" + deterministic_markdown(mode, context)


def _progress_event(step: str, message: str) -> dict[str, Any]:
    return {"type": "progress", "step": step, "message": message}


def handle_prompt_stream(
    prompt: str,
    *,
    mode: str | None = None,
    ticker: str | None = None,
    use_llm: bool = True,
    locale: str = "zh",
) -> Iterator[dict[str, Any]]:
    """SSE-friendly event stream: progress → structured result → optional LLM tokens."""
    from serenity_twin.llm_stream import stream_chat_completion
    from serenity_twin.ui_render import build_structured, render_agent_slot, render_html

    mode = mode or detect_mode(prompt)
    ticker = ticker or extract_ticker(prompt)
    ui_locale = locale if locale in ("en", "zh") else "zh"
    prompt_locale = detect_prompt_locale(prompt, ui_locale)
    llm_available = load_deepseek_key() is not None

    yield _progress_event("route", f"Mode {mode}" + (f" · ${ticker}" if ticker else ""))

    if mode == "B":
        yield _progress_event("radar", "Computing attention radar…")
    elif mode == "brief":
        yield _progress_event("brief", "Loading daily brief…")
    elif mode != "E":
        yield _progress_event("corpus", "Loading Serenity corpus…")

    if mode in ("A", "B", "C", "D"):
        yield _progress_event("live_web", "Running live web research…")

    ctx = build_context(mode, prompt, ticker)
    if mode not in ("E", "brief"):
        yield _progress_event("stale", "Checking thesis freshness…")

    yield _progress_event("render", "Building structured report…")

    ctx["locale"] = prompt_locale
    structured = build_structured(ctx, mode, prompt_locale, suppress_synthesis=llm_available and use_llm)
    html_report = render_html(structured)
    agent_slot = render_agent_slot(prompt_locale, hidden=not (llm_available and use_llm))
    html_with_slot = html_report.replace('<div class="report">', f'<div class="report">{agent_slot}', 1)

    base_result = {
        "mode": mode,
        "ticker": ticker,
        "locale": prompt_locale,
        "llm_used": False,
        "deepseek_available": load_deepseek_key() is not None,
        "live_web_used": "live_web" in ctx,
        "context": ctx,
        "structured": structured,
        "html": html_with_slot,
        "markdown": deterministic_markdown(mode, ctx),
    }
    yield {"type": "result", "data": base_result}

    llm_narrative = ""
    if use_llm and load_deepseek_key():
        yield _progress_event("llm", "Agent synthesis (same path as Cursor SKILL)…")
        try:
            ctx["locale"] = prompt_locale
            for token in stream_chat_completion(prompt, ctx):
                llm_narrative += token
                yield {"type": "token", "text": token}
            if llm_narrative:
                from serenity_twin.agent_output import check_answer_locale

                base_result["llm_used"] = True
                base_result["markdown"] = llm_narrative
                base_result["llm_narrative"] = llm_narrative
                base_result["locale_issues"] = check_answer_locale(llm_narrative, prompt_locale)
        except Exception as exc:
            yield {"type": "error", "message": str(exc)}

    yield {"type": "done", "data": base_result}


def handle_prompt(
    prompt: str,
    *,
    mode: str | None = None,
    ticker: str | None = None,
    use_llm: bool = True,
    locale: str = "zh",
) -> dict[str, Any]:
    mode = mode or detect_mode(prompt)
    ticker = ticker or extract_ticker(prompt)
    ctx = build_context(mode, prompt, ticker)
    ui_locale = locale if locale in ("en", "zh") else "zh"
    prompt_locale = detect_prompt_locale(prompt, ui_locale)
    llm_available = load_deepseek_key() is not None

    from serenity_twin.ui_render import build_structured, render_agent_slot, render_html, render_llm_markdown

    ctx["locale"] = prompt_locale
    structured = build_structured(ctx, mode, prompt_locale, suppress_synthesis=llm_available and use_llm)
    html_report = render_html(structured)
    agent_slot = render_agent_slot(prompt_locale, hidden=not (llm_available and use_llm))
    html_core = html_report.replace('<div class="report">', f'<div class="report">{agent_slot}', 1)

    llm_used = False
    markdown = deterministic_markdown(mode, ctx)
    llm_narrative = ""
    locale_issues: list[str] = []
    if use_llm and llm_available:
        llm_out = chat_completion(prompt, ctx)
        if llm_out and not llm_out.startswith("LLM error"):
            from serenity_twin.agent_output import check_answer_locale

            locale_issues = check_answer_locale(llm_out, prompt_locale)
            markdown = llm_out
            llm_narrative = llm_out
            llm_used = True

    html_final = html_core
    if llm_narrative:
        narrative_html = render_llm_markdown(llm_narrative)
        html_final = html_core.replace(
            '<div class="llm-narrative agent-narrative"></div>',
            f'<div class="llm-narrative agent-narrative">{narrative_html}</div>',
        ).replace("llm-narrative-section hidden", "llm-narrative-section")

    return {
        "mode": mode,
        "ticker": ticker,
        "locale": prompt_locale,
        "llm_used": llm_used,
        "deepseek_available": load_deepseek_key() is not None,
        "live_web_used": "live_web" in ctx,
        "context": ctx,
        "structured": structured,
        "html": html_final,
        "markdown": markdown,
        "llm_narrative": llm_narrative,
        "locale_issues": locale_issues,
    }
