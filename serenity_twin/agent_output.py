"""Lightweight checks on agent narrative output (browser LLM path)."""

from __future__ import annotations

import re

# Mode A section titles that must not appear in English answers
_EN_FORBIDDEN_HEADERS = (
    "她的观点",
    "小白解释",
    "第一性原理",
    "Buffett 直接判断",
    "主要风险",
    "什么情况说明判断错了",
)


def check_answer_locale(text: str, expected: str) -> list[str]:
    """Return human-readable issues when answer language drifts from expected."""
    if not text or expected not in ("en", "zh"):
        return []
    issues: list[str] = []
    if expected == "en":
        for header in _EN_FORBIDDEN_HEADERS:
            if header in text:
                issues.append(f"Chinese section header in English answer: {header}")
        cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        if cn_chars >= 12:
            issues.append(f"Unexpected Chinese text in English answer ({cn_chars} chars)")
    elif expected == "zh":
        en_only_headers = ("Serenity's corpus view", "Plain-language summary", "Key risks")
        for header in en_only_headers:
            if header in text:
                issues.append(f"English-only section header in Chinese answer: {header}")
    return issues
