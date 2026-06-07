"""Tests for stale thesis detection."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.stale_check import assess_stale, extract_corpus_dates


def test_extract_dates_from_thesis():
    text = "Latest stance (May 2026): hold. through ~2026-06-02. auto-distilled 2026-05-28"
    dates = extract_corpus_dates(text)
    assert date(2026, 6, 2) in dates


def test_stale_when_old_and_big_price_move():
    result = assess_stale(
        thesis_markdown="Latest stance May 1, 2025 — long $SIVE",
        quote={
            "regular_market_price": 80.0,
            "price_history": {
                "labels": ["2025-05-01", "2026-06-01"],
                "values": [40.0, 80.0],
            },
        },
        as_of=date(2026, 6, 7),
        stale_days=60,
        stale_price_pct=15.0,
    )
    assert result["stale"] is True
    assert result["level"] == "stale"


def test_fresh_when_recent_corpus():
    result = assess_stale(
        thesis_markdown="through ~2026-06-02",
        quote={"regular_market_price": 78.0, "price_history": {"labels": ["2026-06-01"], "values": [77.0]}},
        as_of=date(2026, 6, 7),
    )
    assert result["stale"] is False
    assert result["level"] == "fresh"
