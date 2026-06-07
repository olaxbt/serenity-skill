#!/usr/bin/env python3
"""Rebuild mention events + summary CSVs from corpus/data/tweets.json (offline-safe)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.config import Settings
from serenity_twin.csv_util import write_csv
from serenity_twin.paths import MENTIONS_EVENTS_CSV, MENTIONS_SUMMARY_CSV, TWEETS_JSON
from serenity_twin.themes import theme_of
from serenity_twin.tickers import count_raw_occurrences, extract_tickers
from serenity_twin.tweets import load_archive, normalize_archive_tweet, parse_time
from serenity_twin.x_api import fetch_recent
from serenity_twin.tweets import merge_tweets

EVENT_HEADERS = [
    "tweet_id",
    "created_at",
    "kind",
    "text",
    "tickers",
    "source_url",
    "conversation_id",
    "referenced_tweet_id",
]

SUMMARY_HEADERS = [
    "rank",
    "ticker",
    "mentioned_posts",
    "raw_occurrences",
    "post_mentions",
    "quote_mentions",
    "reply_mentions",
    "first_seen",
    "last_seen",
    "primary_theme",
    "research_priority",
    "example_url",
]


def _priority(posts: int) -> str:
    if posts >= 50:
        return "high"
    if posts >= 15:
        return "medium"
    if posts >= 5:
        return "watchlist"
    return "low"


def events_from_archive(settings: Settings) -> list[dict[str, str]]:
    archive = load_archive(TWEETS_JSON)
    events = [normalize_archive_tweet(t, settings.handle) for t in archive if t.get("id")]
    # Dedupe by tweet_id, keep longer text
    by_id: dict[str, dict[str, str]] = {}
    for ev in events:
        existing = by_id.get(ev["tweet_id"])
        if not existing or len(ev.get("text", "")) > len(existing.get("text", "")):
            by_id[ev["tweet_id"]] = ev
    return sorted(by_id.values(), key=lambda e: e.get("created_at") or "")


def summarize(events: list[dict[str, str]]) -> list[dict[str, str | int]]:
    by_ticker: dict[str, dict] = {}
    for event in events:
        kind = event.get("kind") or "post"
        text = event.get("text") or ""
        tickers = list(dict.fromkeys(extract_tickers(text) or event.get("tickers", "").split("|")))
        for ticker in tickers:
            if ticker not in by_ticker:
                by_ticker[ticker] = {
                    "ticker": ticker,
                    "mentioned_posts": 0,
                    "raw_occurrences": 0,
                    "post_mentions": 0,
                    "quote_mentions": 0,
                    "reply_mentions": 0,
                    "first_seen": event["created_at"],
                    "last_seen": event["created_at"],
                    "sample_texts": [],
                    "example_url": event.get("source_url", ""),
                }
            row = by_ticker[ticker]
            row["mentioned_posts"] += 1
            row["raw_occurrences"] += max(1, count_raw_occurrences(text, ticker))
            if kind == "reply":
                row["reply_mentions"] += 1
            elif kind == "quote":
                row["quote_mentions"] += 1
            else:
                row["post_mentions"] += 1
            if event["created_at"] < row["first_seen"]:
                row["first_seen"] = event["created_at"]
            if event["created_at"] > row["last_seen"]:
                row["last_seen"] = event["created_at"]
                row["example_url"] = event.get("source_url", "")
            if len(row["sample_texts"]) < 8:
                row["sample_texts"].append(text)

    summary = sorted(
        by_ticker.values(),
        key=lambda r: (-r["mentioned_posts"], -r["raw_occurrences"], r["ticker"]),
    )
    out = []
    for idx, row in enumerate(summary, start=1):
        theme = theme_of(row["ticker"], " ".join(row["sample_texts"]))
        out.append(
            {
                "rank": idx,
                "ticker": row["ticker"],
                "mentioned_posts": row["mentioned_posts"],
                "raw_occurrences": row["raw_occurrences"],
                "post_mentions": row["post_mentions"],
                "quote_mentions": row["quote_mentions"],
                "reply_mentions": row["reply_mentions"],
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"],
                "primary_theme": theme,
                "research_priority": _priority(row["mentioned_posts"]),
                "example_url": row["example_url"],
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild mention analytics from corpus tweets")
    parser.add_argument("--sync-first", action="store_true", help="Run optional X API sync before rebuild")
    parser.add_argument("--include-replies", action="store_true")
    args = parser.parse_args()

    settings = Settings.load()
    if args.sync_first and settings.twitter_sync_enabled:
        payload = fetch_recent(settings, args.include_replies, settings.lookback_hours, settings.max_tweets)
        if payload.get("status") == "ok":
            archive = load_archive(TWEETS_JSON)
            merged, new_count = merge_tweets(archive, payload.get("tweets") or [])
            TWEETS_JSON.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Synced NEW={new_count} CORPUS={len(merged)}")
        else:
            print(payload.get("message") or payload.get("status"))

    events = events_from_archive(settings)
    summary = summarize(events)
    write_csv(MENTIONS_EVENTS_CSV, EVENT_HEADERS, events)
    write_csv(MENTIONS_SUMMARY_CSV, SUMMARY_HEADERS, summary)
    print(f"EVENTS={len(events)} TICKERS={len(summary)}")
    print(f"Wrote {MENTIONS_EVENTS_CSV}")
    print(f"Wrote {MENTIONS_SUMMARY_CSV}")


if __name__ == "__main__":
    main()
