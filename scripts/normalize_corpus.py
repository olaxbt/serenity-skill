#!/usr/bin/env python3
"""One-time / maintenance: unify tweet files to canonical tweets.json + remove legacy duplicates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.paths import LEGACY_TWEETS_CSV, LEGACY_TWEETS_JSON, TICKER_STATS, TWEETS_CSV, TWEETS_JSON
from serenity_twin.schema import to_canonical
from serenity_twin.tweets import load_archive, merge_tweets, write_archive, write_ticker_stats


def main() -> None:
    rows: list = []
    if TWEETS_JSON.exists():
        rows = load_archive(TWEETS_JSON)
    if LEGACY_TWEETS_JSON.exists():
        legacy = load_archive(LEGACY_TWEETS_JSON)
        rows, added = merge_tweets(rows, legacy)
        print(f"Merged legacy aleabitoreddit_tweets.json (+{added} new ids)")
    if not rows:
        raise SystemExit("No tweet archive found.")

    write_archive(rows, TWEETS_JSON, TWEETS_CSV)
    write_ticker_stats(rows, TICKER_STATS)

    for legacy in (LEGACY_TWEETS_JSON, LEGACY_TWEETS_CSV):
        if legacy.exists():
            legacy.unlink()
            print(f"Removed legacy {legacy.name}")

    print(f"CANONICAL={len(rows)} -> {TWEETS_JSON}")


if __name__ == "__main__":
    main()
