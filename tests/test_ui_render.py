"""UI structured render tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_render import build_structured, render_html


def test_build_structured_ticker_en():
    ctx = {
        "ticker": "SIVE",
        "lookup": {
            "found_in_theses": True,
            "thesis": {"sector": "Optical", "file": "theses/x.md", "markdown": "## SIVE\n\n- Thesis bullet"},
            "recent_tweets": [{"created_at": "2026-06-01", "kind": "post", "url": "https://x.com/a", "text_preview": "test"}],
        },
        "live_web": {
            "quote": {
                "status": "ok",
                "regular_market_price": 78.8,
                "currency": "SEK",
                "change_pct_1d": 1.2,
                "price_history": {"labels": ["a"], "values": [1]},
            },
            "news_search": [{"title": "News", "url": "https://example.com", "snippet": "snip"}],
        },
    }
    s = build_structured(ctx, "A", "en")
    html = render_html(s)
    assert "$SIVE" in html
    assert "data-table" in html
    assert "price-chart" in html
    assert "tweet-card" in html


def test_build_structured_zh():
    ctx = {"ticker": "NVTS", "lookup": {"found_in_theses": False, "recent_tweets": []}, "live_web": {}}
    s = build_structured(ctx, "A", "zh")
    types = [sec.get("type") for sec in s["sections"]]
    nested = []
    for sec in s["sections"]:
        if sec.get("type") in ("group", "collapsible"):
            nested.extend(c.get("type") for c in sec.get("sections", []))
    assert "alert" in nested or "alert" in types
