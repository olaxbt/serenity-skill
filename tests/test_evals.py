"""Evaluation tests against evals/ticker-lookup.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lookup_ticker import lookup


@pytest.fixture(scope="module")
def eval_cases():
    path = ROOT / "evals" / "ticker-lookup.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.parametrize("case", yaml.safe_load((ROOT / "evals" / "ticker-lookup.yaml").read_text())["cases"], ids=lambda c: c["ticker"])
def test_lookup_ticker(case):
    result = lookup(case["ticker"], include_radar=False, recent_limit=3)
    assert result["found_in_theses"] == case["must_found"]
    if case["must_found"]:
        md = (result.get("thesis") or {}).get("markdown") or ""
        sector = (result.get("thesis") or {}).get("sector") or ""
        if case.get("sector_contains"):
            assert case["sector_contains"].lower() in sector.lower()
        for phrase in case.get("markdown_contains", []):
            assert phrase.lower() in md.lower(), f"missing '{phrase}' in thesis for {case['ticker']}"
