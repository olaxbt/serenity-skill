"""Unit tests for core serenity_twin utilities."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.distill import classify_tweet
from serenity_twin.schema import to_canonical
from serenity_twin.tickers import extract_tickers


def test_extract_tickers():
    assert "SIVE" in extract_tickers("Long $SIVE for CPO")
    assert "AXTI" in extract_tickers("The Strait of $AXTI")


def test_to_canonical_legacy():
    raw = {
        "id": "123",
        "text": "Test $NVDA",
        "createdAtISO": "2026-01-01T00:00:00+00:00",
        "metrics": {"likes": 1},
    }
    c = to_canonical(raw)
    assert c["id"] == "123"
    assert c["created_at"].startswith("2026")
    assert "NVDA" in c["tickers"]
    assert c["metrics"]["likes"] == 1


def test_classify_thesis():
    c = classify_tweet(
        to_canonical({"id": "1", "text": "Long $SIVE — bottleneck thesis, adding position", "created_at": "2026-06-01T00:00:00+00:00"})
    )
    assert c["category"] == "ticker-thesis"


def test_classify_skip():
    c = classify_tweet(to_canonical({"id": "2", "text": "lol", "created_at": "2026-06-01T00:00:00+00:00", "kind": "reply"}))
    assert c["category"] == "skip"
