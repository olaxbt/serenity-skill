"""Deterministic stale-thesis detection: corpus date vs live price."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

STALE_DAYS_DEFAULT = 60
STALE_PRICE_PCT_DEFAULT = 15.0

MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _parse_iso(s: str) -> date | None:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def extract_corpus_dates(text: str) -> list[date]:
    """Pull plausible stance dates from thesis markdown."""
    if not text:
        return []
    found: list[date] = []

    for m in re.finditer(r"\b(20\d{2}-\d{2}-\d{2})\b", text):
        d = _parse_iso(m.group(1))
        if d:
            found.append(d)

    for m in re.finditer(r"through ~?(20\d{2}-\d{2}-\d{2})", text, re.I):
        d = _parse_iso(m.group(1))
        if d:
            found.append(d)

    for m in re.finditer(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})\b",
        text,
        re.I,
    ):
        mo = MONTH_MAP.get(m.group(1).lower()[:3])
        if mo:
            try:
                found.append(date(int(m.group(3)), mo, int(m.group(2))))
            except ValueError:
                pass

    for m in re.finditer(r"Latest stance \(auto-distilled (20\d{2}-\d{2}-\d{2})\)", text):
        d = _parse_iso(m.group(1))
        if d:
            found.append(d)

    return found


def latest_tweet_date(recent_tweets: list[dict]) -> date | None:
    dates: list[date] = []
    for t in recent_tweets:
        d = _parse_iso(t.get("created_at") or "")
        if d:
            dates.append(d)
    return max(dates) if dates else None


def price_change_since(history: dict[str, Any] | None, since: date, current_price: float | None) -> float | None:
    """Estimate % change from first close on/after `since` to current."""
    if not history or current_price is None:
        return None
    labels = history.get("labels") or []
    values = history.get("values") or []
    if not labels or not values:
        return None

    baseline: float | None = None
    for label, val in zip(labels, values):
        d = _parse_iso(label)
        if d and d >= since and val is not None:
            baseline = float(val)
            break
    if baseline is None and values:
        baseline = float(values[0])
    if baseline is None or abs(baseline) < 1e-9:
        return None
    return round((float(current_price) - baseline) / baseline * 100, 2)


def assess_stale(
    *,
    thesis_markdown: str | None,
    quote: dict[str, Any] | None,
    recent_tweets: list[dict] | None = None,
    as_of: date | None = None,
    stale_days: int = STALE_DAYS_DEFAULT,
    stale_price_pct: float = STALE_PRICE_PCT_DEFAULT,
) -> dict[str, Any]:
    """
    Returns stale assessment dict for UI / lookup JSON.

    Rules (match SKILL.md):
    - stale if latest corpus date is > stale_days ago AND
      abs(price change since corpus) >= stale_price_pct (when price data exists)
    - if price data missing but age > stale_days and no recent tweets, soft stale
    """
    as_of = as_of or date.today()
    recent_tweets = recent_tweets or []
    quote = quote or {}

    thesis_dates = extract_corpus_dates(thesis_markdown or "")
    tweet_date = latest_tweet_date(recent_tweets)
    candidates = thesis_dates + ([tweet_date] if tweet_date else [])
    latest_corpus = max(candidates) if candidates else None

    age_days: int | None = None
    if latest_corpus:
        age_days = (as_of - latest_corpus).days

    current_price = quote.get("regular_market_price")
    history = quote.get("price_history")
    price_chg: float | None = None
    if latest_corpus and current_price is not None:
        price_chg = price_change_since(history, latest_corpus, float(current_price))

    reasons: list[str] = []
    stale = False
    level = "ok"

    if latest_corpus is None:
        reasons.append("no_dated_corpus")
    elif age_days is not None and age_days > stale_days:
        reasons.append(f"corpus_age_{age_days}d_gt_{stale_days}d")
        if price_chg is not None and abs(price_chg) >= stale_price_pct:
            reasons.append(f"price_move_{price_chg:+.1f}pct_since_corpus")
            stale = True
            level = "stale"
        elif price_chg is None:
            reasons.append("price_history_unavailable_soft_stale")
            stale = True
            level = "stale_soft"
        else:
            reasons.append(f"price_move_{price_chg:+.1f}pct_below_{stale_price_pct}pct_threshold")
            level = "watch"
    else:
        level = "fresh"

    return {
        "stale": stale,
        "level": level,
        "reasons": reasons,
        "latest_corpus_date": latest_corpus.isoformat() if latest_corpus else None,
        "age_days": age_days,
        "price_change_pct_since_corpus": price_chg,
        "threshold_days": stale_days,
        "threshold_price_pct": stale_price_pct,
        "latest_tweet_date": tweet_date.isoformat() if tweet_date else None,
    }
