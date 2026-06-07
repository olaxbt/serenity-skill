#!/usr/bin/env python3
"""Merge optional fetch into canonical corpus/data/tweets.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.config import Settings
from serenity_twin.paths import TICKER_STATS, TWEETS_CSV, TWEETS_JSON
from serenity_twin.tweets import load_archive, merge_tweets, write_archive, write_ticker_stats
from serenity_twin.x_api import fetch_recent


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync corpus tweets (optional X API / syndication)")
    parser.add_argument("--include-replies", action="store_true")
    parser.add_argument("--force-offline", action="store_true")
    parser.add_argument("--distill", action="store_true", help="Run distill_candidates after sync")
    args = parser.parse_args()

    settings = Settings.load()
    archive = load_archive(TWEETS_JSON)

    if args.force_offline or not settings.twitter_sync_enabled:
        print(settings.sync_status_message())
        print(f"CORPUS={len(archive)} NEW=0")
        return

    payload = fetch_recent(settings, args.include_replies, settings.lookback_hours, settings.max_tweets)
    if payload.get("status") != "ok":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(0 if payload.get("status") == "disabled" else 1)

    incoming = payload.get("tweets") or []
    merged, new_count = merge_tweets(archive, incoming)
    write_archive(merged, TWEETS_JSON, TWEETS_CSV)
    write_ticker_stats(merged, TICKER_STATS)
    print(f"SOURCE={payload.get('source')} CORPUS={len(merged)} NEW={new_count}")

    if args.distill and new_count > 0:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "agent_distill.py"), "--since-sync"],
            cwd=str(ROOT),
            check=False,
        )


if __name__ == "__main__":
    main()
