"""E2E output structure tests — prompt pipeline must produce charts/tables."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_chat import handle_prompt


def _section_types(result: dict) -> list[str]:
    types: list[str] = []

    def walk(sections: list) -> None:
        for s in sections:
            types.append(s.get("type"))
            if s.get("type") in ("group", "collapsible"):
                walk(s.get("sections", []))

    walk(result.get("structured", {}).get("sections", []))
    return types


def test_mode_a_sive_has_table_and_chart():
    result = handle_prompt(
        "What is Serenity's view on $SIVE?",
        mode="A",
        ticker="SIVE",
        use_llm=False,
        locale="en",
    )
    types = _section_types(result)
    assert "table" in types, f"expected market table, got {types}"
    assert "chart" in types, f"expected price chart, got {types}"
    assert result["live_web_used"] is True


def test_mode_a_includes_stale_assessment():
    result = handle_prompt(
        "Serenity view on $SIVE",
        mode="A",
        ticker="SIVE",
        use_llm=False,
        locale="en",
    )
    stale = result.get("context", {}).get("stale")
    assert stale is not None
    assert "latest_corpus_date" in stale
    assert "level" in stale


def test_mode_b_radar_has_tables():
    result = handle_prompt(
        "Run radar 14 day window",
        mode="B",
        use_llm=False,
        locale="en",
    )
    types = _section_types(result)
    assert types.count("table") >= 1


def test_mode_a_unknown_ticker_has_alert_not_chart_required():
    result = handle_prompt(
        "Analyze $ZZZZZZ fresh name",
        mode="A",
        ticker="ZZZZ",
        use_llm=False,
        locale="en",
    )
    types = _section_types(result)
    assert "alert" in types or "table" in types
