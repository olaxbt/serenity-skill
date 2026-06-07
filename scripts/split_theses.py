#!/usr/bin/env python3
"""Split corpus/references/theses.md into sector files + theses-index.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.paths import REFERENCES
from serenity_twin.theses_index import write_split_theses


def main() -> None:
    source = REFERENCES / "theses.md"
    if not source.exists():
        raise SystemExit(f"Missing {source}")
    stats = write_split_theses(source)
    print(f"SECTORS={stats['sectors']} TICKERS={stats['tickers']}")


if __name__ == "__main__":
    main()
