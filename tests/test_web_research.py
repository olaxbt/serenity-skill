"""Web research unit tests (mocked HTTP)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.web_research import fetch_quote, format_live_web_markdown, yahoo_symbol


def test_yahoo_symbol_ashare():
    assert yahoo_symbol("600519").endswith(".SS")
    assert yahoo_symbol("000001").endswith(".SZ")


def test_yahoo_symbol_btc_maps_to_crypto_spot():
    """BTC on Yahoo is an ETF (~$27); BTC-USD is Bitcoin spot."""
    assert yahoo_symbol("BTC") == "BTC-USD"
    assert yahoo_symbol("ETH") == "ETH-USD"


def test_fetch_quote_btc_requests_spot_not_etf():
    fake = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "shortName": "Bitcoin USD",
                        "exchangeName": "CCC",
                        "regularMarketPrice": 105000.0,
                        "previousClose": 104000.0,
                        "regularMarketTime": 1700000000,
                    },
                    "timestamp": [1700000000],
                    "indicators": {"quote": [{"close": [105000.0]}]},
                }
            ]
        }
    }
    urls: list[str] = []

    def capture(url: str) -> str:
        urls.append(url)
        return json.dumps(fake)

    with patch("serenity_twin.web_research._http_get", side_effect=capture):
        q = fetch_quote("BTC")
    assert urls and "BTC-USD" in urls[0]
    assert "chart/BTC?" not in urls[0]
    assert q["status"] == "ok"
    assert q["instrument_type"] == "crypto_spot"
    assert q["yahoo_symbol"] == "BTC-USD"


def test_fetch_quote_parses_json():
    fake = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "regularMarketPrice": 10.5,
                        "previousClose": 10.0,
                        "regularMarketTime": 1700000000,
                    }
                }
            ]
        }
    }

    with patch("serenity_twin.web_research._http_get", return_value=json.dumps(fake)):
        q = fetch_quote("TEST")
    assert q["status"] == "ok"
    assert q["regular_market_price"] == 10.5
    assert q["change_pct_1d"] == 5.0


def test_format_live_web_markdown():
    md = format_live_web_markdown(
        {
            "fetched_at": "2026-06-07T00:00:00+00:00",
            "quote": {"status": "ok", "regular_market_price": 1.23, "currency": "USD", "change_pct_1d": 2.1},
            "news_search": [{"title": "News", "url": "https://example.com", "snippet": "test"}],
        }
    )
    assert "Live web research" in md
    assert "1.23" in md
