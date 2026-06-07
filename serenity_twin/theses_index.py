"""Parse and index split thesis files."""

from __future__ import annotations

import json
import re
from pathlib import Path

from serenity_twin.paths import REFERENCES, THESIS_DIR, THESIS_INDEX

SECTOR_HEADER = re.compile(r"^##\s+(.+)$")
TICKER_LINE = re.compile(r"^###\s+(.+)$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = SLUG_RE.sub("-", s).strip("-")
    return s or "other"


def extract_tickers_from_header(line: str) -> list[str]:
    """Parse ### LINE — extract primary tickers like SIVE, SIVE/SIVEF, LITE."""
    body = line[4:].strip() if line.startswith("###") else line
    lower = body.lower()
    if any(skip in lower for skip in ("other ", "tier list", "snapshot", "mentions", "see ai")):
        return []
    head = body.split("—")[0].strip()
    if "—" not in body and " - " in body:
        head = body.split(" - ")[0].strip()
    head = head.split("(")[0].strip()
    parts = re.split(r"\s*/\s*", head)
    tickers = []
    for p in parts:
        token = p.strip().split()[0] if p.strip() else ""
        token = re.sub(r"[^A-Z0-9.]", "", token.upper())
        if token and re.match(r"^[A-Z][A-Z0-9.]{0,11}$", token):
            tickers.append(token)
    return tickers


def split_theses_markdown(source: Path) -> tuple[dict[str, str], dict[str, dict]]:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()

    preamble: list[str] = []
    sectors: dict[str, list[str]] = {}
    sector_titles: dict[str, str] = {}
    index: dict[str, dict] = {}

    current_slug: str | None = None
    in_preamble = True

    for line in lines:
        sector_m = SECTOR_HEADER.match(line)
        if sector_m and not line.startswith("## Table"):
            title = sector_m.group(1).strip()
            if title.lower() == "table of contents":
                continue
            current_slug = slugify(title)
            sector_titles[current_slug] = title
            sectors[current_slug] = [f"## {title}", ""]
            in_preamble = False
            continue

        if in_preamble:
            if line.startswith("## Table"):
                continue
            preamble.append(line)
            continue

        if current_slug is None:
            continue

        sectors[current_slug].append(line)

        if TICKER_LINE.match(line):
            for ticker in extract_tickers_from_header(line):
                index[ticker] = {
                    "ticker": ticker,
                    "sector": sector_titles[current_slug],
                    "sector_slug": current_slug,
                    "title": line[4:].strip(),
                    "file": f"theses/{current_slug}.md",
                }

    preamble_text = "\n".join(preamble).strip() + "\n\n"
    bodies = {slug: preamble_text + "\n".join(body).strip() + "\n" for slug, body in sectors.items()}
    return bodies, index


def write_split_theses(source: Path | None = None) -> dict[str, int]:
    source = source or (REFERENCES / "theses.md")
    THESIS_DIR.mkdir(parents=True, exist_ok=True)
    bodies, index = split_theses_markdown(source)
    for slug, body in bodies.items():
        (THESIS_DIR / f"{slug}.md").write_text(body, encoding="utf-8")
    THESIS_INDEX.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "theses.md",
                "sector_count": len(bodies),
                "ticker_count": len(index),
                "tickers": index,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"sectors": len(bodies), "tickers": len(index)}


def load_index() -> dict:
    if not THESIS_INDEX.exists():
        return {"tickers": {}}
    return json.loads(THESIS_INDEX.read_text(encoding="utf-8"))


def get_ticker_section(ticker: str) -> dict | None:
    ticker = ticker.upper().lstrip("$")
    data = load_index()
    tickers = data.get("tickers", {})

    entry = tickers.get(ticker)
    if not entry:
        for key, val in tickers.items():
            if ticker in key.upper() or ticker in val.get("title", "").upper():
                entry = val
                break
    if not entry:
        return None

    path = REFERENCES / entry["file"]
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?=^###\s)", content, flags=re.MULTILINE)
    section = None
    for block in blocks:
        first = block.splitlines()[0] if block.splitlines() else ""
        if not first.startswith("###"):
            continue
        header_upper = first.upper()
        if f" {ticker} " in f" {header_upper} " or header_upper.startswith(f"### {ticker}") or f"/{ticker}" in header_upper:
            section = block.strip()
            break
    if not section:
        return None
    return {**entry, "section_markdown": section}
