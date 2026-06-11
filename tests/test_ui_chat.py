"""UI chat routing tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_chat import build_context, detect_mode, extract_ticker, resolve_ticker


def test_detect_mode_radar():
    assert detect_mode("她最近在 ramp 什么？跑 radar") == "B"


def test_detect_mode_fresh_ticker():
    assert detect_mode("Serenity 怎么看 $NVTS") == "A"
    assert extract_ticker("用 serenity-twin：$SIVE 观点") == "SIVE"


def test_detect_mode_deep_scan_theme():
    prompt = "Deep scan US STOCK AI semiconductor chain: scarce layers first, then stocks and ETF fit."
    assert detect_mode(prompt) == "C"


def test_mode_c_ignores_deep_word_as_ticker():
    prompt = "Deep scan US STOCK AI semiconductor chain: scarce layers first, then stocks and ETF fit."
    assert resolve_ticker(prompt, "C") is None
    assert extract_ticker(prompt, explicit_only=True) is None


def test_mode_c_build_context_uses_theme_not_single_ticker():
    prompt = "Deep scan US STOCK AI semiconductor chain: scarce layers first, then stocks and ETF fit."
    ctx = build_context("C", prompt, None)
    assert ctx.get("ticker") is None
    assert "quote" not in (ctx.get("live_web") or {})
    assert (ctx.get("live_web") or {}).get("query")
