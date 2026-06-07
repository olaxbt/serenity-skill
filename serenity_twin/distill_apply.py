"""Apply distill candidates to corpus files (agent-automated path)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from serenity_twin.llm import summarize_thesis_delta
from serenity_twin.paths import DISTILL_CANDIDATES, REFERENCES
from serenity_twin.theses_index import get_ticker_section, write_split_theses


def _month_section_id(iso_date: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    except ValueError:
        return "## 2026-06"
    y, m = dt.year, dt.month
    if m <= 3:
        return f"## {y}-01 to {y}-03" if m == 1 else f"## {y}-03"
    if m <= 5:
        return f"## {y}-04 to {y}-05"
    if m == 6:
        return f"## {y}-06"
    return f"## {y}-{m:02d}"


def append_track_record(entry: dict) -> bool:
    path = REFERENCES / "track-record.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    date = (entry.get("created_at") or "")[:10]
    tickers = entry.get("tickers") or []
    ticker = tickers[0] if tickers else "—"
    url = entry.get("url") or ""
    preview = (entry.get("text_preview") or "").replace("|", " ")[:120]
    row = f"| {date} | {ticker} | {preview} ([source]({url})) | auto-logged; verify outcome |"

    section = _month_section_id(entry.get("created_at") or "")
    if section not in text:
        text = text.rstrip() + f"\n\n{section}\n\n| Date | Ticker | Call | Outcome (as he reported) |\n|---|---|---|---|\n{row}\n"
    else:
        # append after section header table's last row before next ##
        parts = text.split(section, 1)
        if len(parts) != 2:
            return False
        rest = parts[1]
        next_h = re.search(r"\n## ", rest)
        if next_h:
            block = rest[: next_h.start()]
            tail = rest[next_h.start() :]
        else:
            block = rest
            tail = ""
        if row in block:
            return False
        block = block.rstrip() + "\n" + row + "\n"
        text = parts[0] + section + block + tail

    path.write_text(text, encoding="utf-8")
    return True


def append_thesis_update(entry: dict, use_llm: bool = True) -> bool:
    tickers = entry.get("tickers") or []
    if not tickers:
        return False
    ticker = tickers[0].upper()
    section_data = get_ticker_section(ticker)
    if not section_data:
        return False

    path = REFERENCES / section_data["file"]
    content = path.read_text(encoding="utf-8")
    date = (entry.get("created_at") or "")[:10]
    url = entry.get("url") or ""
    preview = entry.get("text_preview") or ""

    delta = None
    if use_llm:
        delta = summarize_thesis_delta(ticker, preview, section_data.get("section_markdown") or "")

    if not delta:
        delta = f"{preview[:200]} ([source]({url}))"

    bullet = f"- **Latest stance (auto-distilled {date}):** {delta}"
    marker = f"### {ticker}" if f"### {ticker} " not in content else None
    # Find block for this ticker
    blocks = re.split(r"(?=^###\s)", content, flags=re.MULTILINE)
    new_blocks = []
    updated = False
    for block in blocks:
        first = block.splitlines()[0] if block.splitlines() else ""
        if first.upper().startswith("###") and ticker in first.upper():
            if bullet not in block:
                block = block.rstrip() + "\n" + bullet + "\n"
                updated = True
        new_blocks.append(block)

    if not updated:
        return False
    path.write_text("".join(new_blocks), encoding="utf-8")
    return True


def apply_candidates(candidates: list[dict], use_llm: bool = True) -> dict[str, int]:
    stats = {"track-record": 0, "ticker-thesis": 0, "skipped": 0, "failed": 0}
    for entry in candidates:
        cat = entry.get("category")
        if cat == "skip" or cat == "data-only":
            stats["skipped"] += 1
            continue
        if cat == "track-record":
            ok = append_track_record(entry)
            stats["track-record"] += int(ok)
            if not ok:
                stats["failed"] += 1
        elif cat == "ticker-thesis":
            ok = append_thesis_update(entry, use_llm=use_llm)
            stats["ticker-thesis"] += int(ok)
            if not ok:
                stats["failed"] += 1
        else:
            stats["skipped"] += 1

    # Refresh index after sector file edits
    master = REFERENCES / "theses.md"
    if master.exists():
        write_split_theses(master)
    return stats
