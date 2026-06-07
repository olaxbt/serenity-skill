"""UI chat routing tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_chat import detect_mode, extract_ticker


def test_detect_mode_radar():
    assert detect_mode("她最近在 ramp 什么？跑 radar") == "B"


def test_detect_mode_fresh_ticker():
    assert detect_mode("Serenity 怎么看 $NVTS") == "A"
    assert extract_ticker("用 serenity-twin：$SIVE 观点") == "SIVE"
