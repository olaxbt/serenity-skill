"""Canonical I/O schema for tweet archive records."""

from __future__ import annotations

from typing import Any

from serenity_twin.tickers import extract_tickers
from serenity_twin.tweet_parse import parse_time, tweet_kind, tweet_text

HANDLE = "aleabitoreddit"


def to_canonical(raw: dict[str, Any], handle: str = HANDLE) -> dict[str, Any]:
    """Normalize legacy or API tweet dicts to the canonical archive schema."""
    tid = str(raw.get("id") or raw.get("tweet_id") or "")
    text = tweet_text(raw) if (raw.get("quotedTweet") or raw.get("quoted_tweet")) else (raw.get("text") or "")
    if not text and raw.get("text"):
        text = str(raw["text"])
    dt = parse_time(raw)
    created_at = dt.isoformat() if dt else str(raw.get("created_at") or raw.get("createdAtISO") or raw.get("createdAt") or "")

    metrics_in = raw.get("metrics") or {}
    if not metrics_in and any(k in raw for k in ("likes", "retweets", "replies")):
        metrics_in = {
            "likes": raw.get("likes", 0),
            "retweets": raw.get("retweets", 0),
            "replies": raw.get("replies", 0),
            "quotes": raw.get("quotes", 0),
            "views": raw.get("views", 0),
        }

    tickers = raw.get("tickers")
    if isinstance(tickers, str):
        tickers_list = [t for t in tickers.split("|") if t]
    elif isinstance(tickers, list):
        tickers_list = tickers
    else:
        tickers_list = extract_tickers(text)

    kind = raw.get("kind") or tweet_kind(raw)
    url = raw.get("url") or raw.get("source_url") or (f"https://x.com/{handle}/status/{tid}" if tid else "")

    return {
        "id": tid,
        "text": text,
        "created_at": created_at,
        "url": url,
        "kind": kind,
        "tickers": tickers_list,
        "metrics": {
            "likes": int(metrics_in.get("likes") or 0),
            "retweets": int(metrics_in.get("retweets") or 0),
            "replies": int(metrics_in.get("replies") or 0),
            "quotes": int(metrics_in.get("quotes") or metrics_in.get("quote_count") or 0),
            "views": int(metrics_in.get("views") or 0),
        },
        "conversation_id": str(raw.get("conversation_id") or raw.get("conversationId") or ""),
        "referenced_tweet_id": str(
            raw.get("referenced_tweet_id")
            or raw.get("inReplyToTweetId")
            or raw.get("replyToTweetId")
            or ""
        ),
    }
