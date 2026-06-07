"""Load SKILL + workflow excerpts for browser UI agent (Cursor-parity prompts)."""

from __future__ import annotations

from serenity_twin.paths import REASONING, ROOT

SKILL = ROOT / "SKILL.md"
MAX_WORKFLOW_CHARS = 6000


def _read(path, limit: int = MAX_WORKFLOW_CHARS) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")[:limit]


_MODE_A_SECTIONS = {
    "en": (
        "Mode A — Ticker view. Use these ## section headers exactly (English only):\n"
        "- Serenity's corpus view\n"
        "- Live verification\n"
        "- Plain-language summary\n"
        "- First-principles check\n"
        "- Buffett-style assessment\n"
        "- Key risks\n"
        "- What would falsify this view"
    ),
    "zh": (
        "Mode A — 单标的观点。使用以下 ## 小节标题（中文）:\n"
        "- 她的观点\n"
        "- Live verification（可保留英文小标题）\n"
        "- 小白解释\n"
        "- 第一性原理\n"
        "- Buffett 直接判断\n"
        "- 主要风险\n"
        "- 什么情况说明判断错了"
    ),
}


def build_agent_system_prompt(mode: str, *, locale: str = "en") -> str:
    """System prompt mirroring Cursor Agent + SKILL.md for the given mode."""
    loc = locale if locale in ("en", "zh") else "en"
    lang_rule = (
        "LANGUAGE (strict): Write the ENTIRE answer — every heading and sentence — in English. "
        "Use only the English section headers listed below for this mode — never Chinese headings from SKILL.md. "
        "Ticker symbols and proper nouns may stay as-is."
        if loc == "en"
        else "LANGUAGE (strict): Write the ENTIRE answer in Chinese. Section headers in Chinese."
    )
    base = (
        "You are Serenity Twin — the same research agent as the Cursor SKILL, running in the browser UI. "
        "Scripts have ALREADY executed: lookup_ticker, live_research (quote/news/SEC), stale_check, radar if needed. "
        "Your job: write the PRIMARY research answer that directly addresses the user's question. "
        "This is the main deliverable — lead with the answer, not process narration. "
        "Rules: reconcile corpus vs live_web; respect stale flags; use evidence-ladder grading; "
        "clearly label Serenity corpus view vs independent verification vs research map; no buy/sell orders. "
        f"{lang_rule} "
        "FORMAT: short ## section headers; tight bullet lists; 1–2 sentence paragraphs max; "
        "no generic AI preamble ('Certainly', 'Great question'); no emoji walls; no numbered essay dumps. "
        + (
            "End with: Research support only. Not investment advice."
            if loc == "en"
            else "End with: 仅作信息跟踪，不构成投资建议。"
        )
    )
    extras: list[str] = []
    if mode == "A":
        extras.append(_MODE_A_SECTIONS[loc])
    elif mode == "B":
        extras.append("Mode B — Radar. Interpret heating, new entrants, conviction, theme rotation; cross-check theses.")
    elif mode == "C":
        wf = _read(REASONING / "references" / "deep-research-workflow.md")
        extras.append(f"Mode C — Theme scan. Follow deep-research-workflow:\n{wf}")
    elif mode == "D":
        tpl = _read(REASONING / "assets" / "thesis-template.md")
        wf = _read(REASONING / "references" / "deep-research-workflow.md", 3000)
        extras.append(f"Mode D — Research memo. Use thesis-template structure:\n{tpl}\n\nWorkflow:\n{wf}")
    elif mode == "E":
        extras.append("Mode E — Learning. One question at a time; teach methodology; no stock picks unless illustrative.")
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
