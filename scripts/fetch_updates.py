#!/usr/bin/env python3
"""Fetch recent tweets from X API v2 (optional).

Exits 0 with status=disabled when X_BEARER_TOKEN is not configured.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.config import Settings
from serenity_twin.x_api import fetch_recent


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch recent @aleabitoreddit posts via X API")
    parser.add_argument("--lookback-hours", type=int, default=None)
    parser.add_argument("--max-tweets", type=int, default=None)
    parser.add_argument("--include-replies", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    settings = Settings.load()
    if not settings.twitter_sync_enabled:
        payload = {
            "status": "disabled",
            "message": settings.sync_status_message(),
            "tweets": [],
        }
    else:
        lookback = args.lookback_hours or settings.lookback_hours
        max_tweets = args.max_tweets or settings.max_tweets
        try:
            payload = fetch_recent(settings, args.include_replies, lookback, max_tweets)
        except Exception as exc:  # noqa: BLE001 — CLI surfaces any fetch failure
            payload = {"status": "error", "message": str(exc), "tweets": []}

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if payload.get("status") == "error":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
