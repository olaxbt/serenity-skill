"""Format deterministic UI reports from lookup / radar / fresh-name flows."""

from __future__ import annotations

from pathlib import Path

from serenity_twin.paths import REFERENCES, ROOT

METHODOLOGY = REFERENCES / "methodology.md"

CHECKLIST_START = "## 15. The checklist"
CHECKLIST_END = "Then: confirm current price"


def _methodology_checklist() -> str:
    if not METHODOLOGY.exists():
        return "(methodology.md not found)"
    text = METHODOLOGY.read_text(encoding="utf-8")
    start = text.find(CHECKLIST_START)
    end = text.find(CHECKLIST_END, start)
    if start == -1:
        return text[-2000:]
    chunk = text[start : end + len(CHECKLIST_END)] if end != -1 else text[start:]
    return chunk.strip()


def format_ticker_report(payload: dict) -> str:
    """Markdown report for Mode A / unknown ticker."""
    ticker = payload.get("ticker", "?")
    lines: list[str] = [f"# ${ticker} — Serenity Twin lookup", ""]

    if payload.get("found_in_theses"):
        th = payload.get("thesis") or {}
        lines.append(f"**Corpus status:** deep thesis in `{th.get('file', '?')}` ({th.get('sector', '')})")
        lines.append("")
        lines.append("## Thesis (corpus)")
        lines.append(th.get("markdown") or "(empty)")
    else:
        lines.append("**Corpus status:** not in `theses-index.json` (no deep distilled thesis).")

    tweets = payload.get("recent_tweets") or []
    if tweets:
        lines.append("")
        lines.append(f"## Recent tweets mentioning ${ticker} ({len(tweets)} shown)")
        for t in tweets:
            lines.append(f"- [{t.get('created_at', '')[:10]}]({t.get('url', '#')}) ({t.get('kind', 'post')}): {t.get('text_preview', '')}")
    else:
        lines.append("")
        lines.append(f"## Tweets: none in archive for ${ticker}")

    radar = payload.get("radar")
    if radar:
        lines.append("")
        lines.append(f"## Radar signal: `{radar.get('signal')}` — recent={radar.get('recent')} velocity={radar.get('velocity', radar.get('delta', '?'))}")

    lines.append("")
    lines.append("---")
    if not payload.get("found_in_theses") and not tweets:
        lines.append("## Fresh-name path (Serenity never covered this ticker)")
        lines.append("")
        lines.append("1. **Lookup** → no thesis, no tweets → `found_in_theses=false`")
        lines.append("2. **Agent / UI** applies `methodology.md` checklist (14 principles + 14 questions below)")
        lines.append("3. **Output tier:** independent analysis — label **not Serenity's stated view**")
        lines.append("4. **Auto:** UI / `live_research.py` fetches quote + news + SEC without user asking")
        lines.append("")
        lines.append("### Methodology checklist (excerpt)")
        lines.append("")
        lines.append(_methodology_checklist())
    elif not payload.get("found_in_theses") and tweets:
        lines.append("## Partial coverage")
        lines.append("")
        lines.append("- Mentioned in tweets but **no deep thesis** — treat tweets as leads; apply checklist for conviction.")
    else:
        lines.append("*Research support only. Confirm current price and fundamentals. Not investment advice.*")

    return "\n".join(lines)


def format_radar_report(result: dict, text: str) -> str:
    return text


def format_daily_brief(path: Path) -> str:
    if not path.exists():
        return "No daily brief yet. Run: `powershell -ExecutionPolicy Bypass -File scripts/daily_brief.ps1`"
    return path.read_text(encoding="utf-8")
