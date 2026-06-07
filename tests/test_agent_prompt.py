"""Agent prompt locale and output checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.agent_output import check_answer_locale
from serenity_twin.agent_prompt import build_agent_system_prompt


def test_english_mode_a_prompt_has_english_sections_only():
    prompt = build_agent_system_prompt("A", locale="en")
    assert "Serenity's corpus view" in prompt
    assert "她的观点" not in prompt.split("SKILL excerpt")[0]
    assert "ignore those" in prompt.lower() or "Do NOT use Chinese" in prompt


def test_chinese_mode_a_prompt_has_chinese_sections():
    prompt = build_agent_system_prompt("A", locale="zh")
    assert "她的观点" in prompt


def test_check_answer_locale_flags_chinese_headers():
    bad = "## 她的观点\n\nLong on SIVE.\n\n## 主要风险\n\nVolatility."
    issues = check_answer_locale(bad, "en")
    assert any("她的观点" in i for i in issues)
