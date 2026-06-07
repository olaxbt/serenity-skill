"""Tweet archive load, normalize, merge, export."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from serenity_twin.schema import to_canonical
from serenity_twin.tickers import extract_tickers
from serenity_twin.tweet_parse import parse_time, tweet_kind

USER = "aleabitoreddit"


def normalize_archive_tweet(tweet: dict[str, Any], handle: str = USER) -> dict[str, str]:
    c = to_canonical(tweet, handle)
    return {
        "tweet_id": c["id"],
        "created_at": c["created_at"],
        "kind": c["kind"],
        "text": c["text"],
        "tickers": "|".join(c["tickers"]),
        "source_url": c["url"],
        "conversation_id": c["conversation_id"],
        "referenced_tweet_id": c["referenced_tweet_id"],
    }


def load_archive(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        return []
    return [to_canonical(t) for t in rows if t.get("id") or t.get("tweet_id")]


def merge_tweets(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    merged = {str(to_canonical(t)["id"]): to_canonical(t) for t in existing if to_canonical(t)["id"]}
    new_count = 0
    for tweet in incoming:
        c = to_canonical(tweet)
        tid = c["id"]
        if not tid:
            continue
        if tid not in merged:
            new_count += 1
        merged[tid] = c
    rows = sorted(
        merged.values(),
        key=lambda t: parse_time(t) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return rows, new_count


def write_archive(rows: list[dict[str, Any]], json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cols = [
        "id", "url", "created_at", "kind", "text", "tickers",
        "likes", "retweets", "replies", "quotes", "views",
        "conversation_id", "referenced_tweet_id",
    ]

    def cell(text: str) -> str:
        return "\n".join(line.rstrip() for line in (text or "").replace("\r", " ").split("\n"))

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for t in rows:
            m = t.get("metrics") or {}
            tickers = t.get("tickers") or []
            w.writerow({
                "id": t.get("id"),
                "url": t.get("url"),
                "created_at": t.get("created_at"),
                "kind": t.get("kind"),
                "text": cell(t.get("text", "")),
                "tickers": "|".join(tickers) if isinstance(tickers, list) else tickers,
                "likes": m.get("likes", 0),
                "retweets": m.get("retweets", 0),
                "replies": m.get("replies", 0),
                "quotes": m.get("quotes", 0),
                "views": m.get("views", 0),
                "conversation_id": t.get("conversation_id", ""),
                "referenced_tweet_id": t.get("referenced_tweet_id", ""),
            })


def write_ticker_stats(rows: list[dict[str, Any]], path: Path) -> None:
    counts: dict[str, int] = {}
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    for tweet in sorted(rows, key=lambda t: parse_time(t) or datetime.min.replace(tzinfo=timezone.utc)):
        text = tweet.get("text") or ""
        tickers = tweet.get("tickers") or extract_tickers(text)
        day = (parse_time(tweet) or datetime.now(timezone.utc)).date().isoformat()
        for ticker in set(tickers):
            u = str(ticker).upper()
            counts[u] = counts.get(u, 0) + 1
            first.setdefault(u, day)
            last[u] = day
    lines = [
        f"Total tweets: {len(rows)}",
        f"Distinct $tickers: {len(counts)}",
        "",
        "ticker  mentions  first_seen  last_seen",
    ]
    for ticker, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        if n >= 2:
            lines.append(f"{ticker:8} {n:6}   {first[ticker]}  {last[ticker]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def recent_tweets_for_ticker(rows: list[dict[str, Any]], ticker: str, limit: int = 5) -> list[dict[str, Any]]:
    ticker = ticker.upper()
    out = []
    for t in rows:
        tickers = [x.upper() for x in (t.get("tickers") or [])]
        if ticker in tickers or f"${ticker}" in (t.get("text") or "").upper():
            out.append(t)
        if len(out) >= limit:
            break
    return out
