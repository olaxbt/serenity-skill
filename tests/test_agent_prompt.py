"""Agent prompt locale and output checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.agent_output import check_answer_locale, check_answer_structure
from serenity_twin.agent_prompt import build_agent_system_prompt


def test_english_mode_a_prompt_has_english_sections_only():
    prompt = build_agent_system_prompt("A", locale="en")
    assert "Serenity's corpus view" in prompt
    assert "Executive summary" in prompt
    assert "她的观点" not in prompt.split("SKILL excerpt")[0]
    assert "ignore those" in prompt.lower() or "never Chinese" in prompt.lower()


def test_chinese_mode_a_prompt_has_chinese_sections():
    prompt = build_agent_system_prompt("A", locale="zh")
    assert "她的观点" in prompt
    assert "执行摘要" in prompt


def test_english_mode_c_prompt_has_layer_sections():
    prompt = build_agent_system_prompt("C", locale="en")
    assert "Value-chain layer ranking" in prompt
    assert "Scarce layers" in prompt
    assert "Research candidates" in prompt


def test_english_mode_b_prompt_has_radar_sections():
    prompt = build_agent_system_prompt("B", locale="en")
    assert "What's heating" in prompt
    assert "Theme rotation" in prompt


def test_check_answer_locale_flags_chinese_headers():
    bad = "## 她的观点\n\nLong on SIVE.\n\n## 主要风险\n\nVolatility."
    issues = check_answer_locale(bad, "en")
    assert any("她的观点" in i for i in issues)


def test_check_answer_structure_requires_executive_summary():
    good = "## Executive summary\n\nSIVE remains core CPO play.\n\n## Serenity's corpus view\n\n- Held"
    assert check_answer_structure(good, "A", "en") == []
    bad = "## Serenity's corpus view\n\nNo summary."
    assert any("Executive summary" in i for i in check_answer_structure(bad, "A", "en"))
