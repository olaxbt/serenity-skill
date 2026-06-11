#!/usr/bin/env python3
"""Deterministic ticker lookup: thesis section + recent tweets + radar hint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.paths import THESIS_INDEX, TWEETS_JSON
from serenity_twin.theses_index import get_ticker_section, load_index
from serenity_twin.tweets import load_archive, recent_tweets_for_ticker


def radar_hint(ticker: str) -> dict | None:
    """In-process radar hint — avoids slow subprocess spawn on every ticker lookup."""
    from datetime import date

    from serenity_twin.csv_util import read_csv
    from serenity_twin.paths import MENTIONS_EVENTS_CSV

    if not MENTIONS_EVENTS_CSV.exists():
        return None
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("radar", ROOT / "scripts" / "radar.py")
        if spec is None or spec.loader is None:
            return None
        radar_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(radar_mod)
        events = read_csv(MENTIONS_EVENTS_CSV)
        dates = sorted({(e.get("created_at") or "")[:10] for e in events if e.get("created_at")})
        asof = dates[-1] if dates else date.today().isoformat()
        data = radar_mod.compute_radar(events, asof, 14, 50)
        for block in ("heating", "new_entrants", "conviction_watch"):
            for row in data.get(block, []):
                if row.get("ticker", "").upper() == ticker.upper():
                    return {"signal": block, **row}
        return None
    except Exception:
        return None


def lookup(ticker: str, include_radar: bool = True, recent_limit: int = 5) -> dict:
    ticker = ticker.upper().lstrip("$")
    result: dict = {
        "ticker": ticker,
        "found_in_theses": False,
        "thesis": None,
        "recent_tweets": [],
        "radar": None,
        "index_meta": None,
    }

    if not THESIS_INDEX.exists():
        result["warning"] = "theses-index.json missing; run scripts/split_theses.py"
    else:
        section = get_ticker_section(ticker)
        if section:
            result["found_in_theses"] = True
            result["thesis"] = {
                "sector": section.get("sector"),
                "sector_slug": section.get("sector_slug"),
                "title": section.get("title"),
                "file": section.get("file"),
                "markdown": section.get("section_markdown"),
            }
        else:
            idx = load_index()
            result["index_meta"] = {"total_tickers": len(idx.get("tickers", {}))}

    if TWEETS_JSON.exists():
        archive = load_archive(TWEETS_JSON)
        result["recent_tweets"] = [
            {
                "id": t["id"],
                "created_at": t["created_at"],
                "url": t["url"],
                "kind": t["kind"],
                "text_preview": (t.get("text") or "")[:280],
            }
            for t in recent_tweets_for_ticker(archive, ticker, recent_limit)
        ]

    if include_radar:
        result["radar"] = radar_hint(ticker)

    if not result["found_in_theses"] and not result["recent_tweets"]:
        result["suggestion"] = "Run methodology checklist from corpus/references/methodology.md"

    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Lookup Serenity thesis + recent tweets for a ticker")
    parser.add_argument("ticker", help="e.g. SIVE or $AXTI")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-radar", action="store_true")
    parser.add_argument("--recent", type=int, default=5)
    args = parser.parse_args()

    payload = lookup(args.ticker, include_radar=not args.no_radar, recent_limit=args.recent)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["found_in_theses"] or payload["recent_tweets"] else 1)


if __name__ == "__main__":
    main()
