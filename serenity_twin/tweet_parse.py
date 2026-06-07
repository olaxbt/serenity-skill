"""Low-level tweet text/time/kind helpers (no schema dependency)."""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


def parse_time(tweet: dict[str, Any]) -> datetime | None:
    for key in ("created_at", "createdAtISO", "createdAt"):
        raw = tweet.get(key)
        if not raw:
            continue
        if key == "createdAt" and "@" in str(raw):
            try:
                return parsedate_to_datetime(str(raw))
            except (TypeError, ValueError):
                continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def tweet_text(tweet: dict[str, Any]) -> str:
    parts = [tweet.get("text") or ""]
    quoted = tweet.get("quotedTweet") or tweet.get("quoted_tweet")
    if isinstance(quoted, dict) and quoted.get("text"):
        parts.append(str(quoted["text"]))
    return " ".join(p for p in parts if p).strip()


def tweet_kind(tweet: dict[str, Any]) -> str:
    if tweet.get("kind") in {"post", "reply", "quote"}:
        return str(tweet["kind"])
    if tweet.get("isReply") or tweet.get("inReplyToTweetId"):
        return "reply"
    if tweet.get("isQuote") or tweet.get("quotedTweet") or tweet.get("quoted_tweet"):
        return "quote"
    refs = tweet.get("referenced_tweets") or tweet.get("referencedTweets") or []
    for ref in refs:
        if ref.get("type") == "replied_to":
            return "reply"
        if ref.get("type") == "quoted":
            return "quote"
    return "post"
