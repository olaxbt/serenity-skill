#!/usr/bin/env python3
"""CLI: automatic live web research for a ticker or theme query."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.web_research import format_live_web_markdown, research_theme, research_ticker  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Live web research (quote + news + SEC)")
    parser.add_argument("target", nargs="?", help="Ticker e.g. SIVE, or theme text in quotes")
    parser.add_argument("--theme", action="store_true", help="Treat target as theme query")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.target:
        parser.error("Provide a ticker or theme query")

    if args.theme:
        payload = research_theme(args.target)
    else:
        payload = research_ticker(args.target)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_live_web_markdown(payload))


if __name__ == "__main__":
    main()
