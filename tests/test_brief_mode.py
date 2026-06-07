"""Daily brief mode tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_chat import detect_mode, handle_prompt


def test_fresh_name_not_detected_as_learning_mode():
    prompt = "Serenity never covered $NVTS deeply. Apply methodology checklist for a fresh-name analysis."
    assert detect_mode(prompt) == "A"


def test_daily_brief_not_detected_as_radar():
    prompt = "Summarize daily brief Heating tickers and corpus views."
    assert detect_mode(prompt) == "brief"


def test_brief_mode_returns_heating_table():
    prompt = "Summarize daily brief Heating tickers and corpus views."
    result = handle_prompt(prompt, mode="brief", use_llm=False, locale="en")
    types = []
    for s in result.get("structured", {}).get("sections", []):
        types.append(s.get("type"))
        if s.get("type") in ("group", "collapsible"):
            types.extend(c.get("type") for c in s.get("sections", []))
    assert result["mode"] == "brief"
    assert "table" in types
    titles = [s.get("title", "") for s in result["structured"]["sections"]]
    assert any("Daily brief" in t or "Heating" in t for t in titles)
