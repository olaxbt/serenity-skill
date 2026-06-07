"""Classify new tweets for thesis distillation."""

from __future__ import annotations

import re
from typing import Any

SKIP_PATTERNS = [
    r"^(lol|lmao|gg|nice|thanks|thank you)\b",
    r"meme|joke|for fun only",
]
THESIS_SIGNALS = [
    r"\blong\b", r"\bshort\b", r"\bbuy\b", r"\bsell\b", r"\bhold\b",
    r"bottleneck", r"chokepoint", r"conviction", r"thesis", r"sold out",
    r"downgrade", r"upgrade", r"trimmed", r"added", r"position",
]
TRACK_RECORD_SIGNALS = [
    r"\+\d+%", r"YTD", r"called it", r"was right", r"entry ~",
]
METHODOLOGY_SIGNALS = [
    r"framework", r"how i think", r"supply chain", r"BOM", r"OSINT",
]


def _matches(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(re.search(p, lower, re.IGNORECASE) for p in patterns)


def classify_tweet(tweet: dict[str, Any]) -> dict[str, Any]:
    text = tweet.get("text") or ""
    tickers = tweet.get("tickers") or []
    kind = tweet.get("kind") or "post"

    if len(text.strip()) < 20 and kind == "reply":
        category = "skip"
        reason = "short_reply"
    elif _matches(text, SKIP_PATTERNS):
        category = "skip"
        reason = "low_signal"
    elif _matches(text, TRACK_RECORD_SIGNALS):
        category = "track-record"
        reason = "dated_call_or_calibration"
    elif tickers and _matches(text, THESIS_SIGNALS):
        category = "ticker-thesis"
        reason = "stance_or_catalyst"
    elif _matches(text, METHODOLOGY_SIGNALS):
        category = "methodology"
        reason = "reusable_principle"
    elif tickers:
        category = "ticker-thesis"
        reason = "ticker_mention"
    else:
        category = "data-only"
        reason = "archive_only"

    return {
        "tweet_id": tweet.get("id"),
        "created_at": tweet.get("created_at"),
        "url": tweet.get("url"),
        "kind": kind,
        "tickers": tickers,
        "category": category,
        "reason": reason,
        "text_preview": text[:240].replace("\n", " "),
        "suggested_actions": _suggested_actions(category, tickers),
    }


def _suggested_actions(category: str, tickers: list[str]) -> list[str]:
    if category == "skip":
        return ["no_skill_update"]
    if category == "data-only":
        return ["already_in_tweets_json"]
    if category == "track-record":
        return ["update corpus/references/track-record.md"]
    if category == "methodology":
        return ["update corpus/references/methodology.md if durable"]
    if category == "ticker-thesis":
        files = [f"update corpus/references/theses/{t}.md via sector file" for t in tickers[:3]]
        return ["update sector file in corpus/references/theses/", "re-run scripts/split_theses.py --merge", *files]
    return []
