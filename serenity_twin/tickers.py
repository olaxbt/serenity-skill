"""Ticker extraction from tweet text."""

from __future__ import annotations

import re

VALID_TICKER = re.compile(r"^[A-Z][A-Z0-9.\-]{0,11}$|^\d{4,5}$")
CASHTAG_RE = re.compile(r"(^|[^A-Za-z0-9_])\$([A-Za-z0-9][A-Za-z0-9.\-]{0,11})(?![A-Za-z0-9_])")


def is_valid_ticker(ticker: str) -> bool:
    return bool(VALID_TICKER.match(ticker))


def extract_tickers(text: str) -> list[str]:
    tickers: set[str] = set()
    for match in CASHTAG_RE.finditer(text or ""):
        ticker = match.group(2).rstrip(".,;:!?").upper()
        if is_valid_ticker(ticker):
            tickers.add(ticker)
    return sorted(tickers)


def count_raw_occurrences(text: str, ticker: str) -> int:
    escaped = re.escape(ticker)
    pattern = re.compile(rf"(^|[^A-Za-z0-9_])\${escaped}(?![A-Za-z0-9_])", re.IGNORECASE)
    return len(pattern.findall(text or ""))
