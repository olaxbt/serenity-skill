"""UI formatting: thesis paragraphing, locale, section hierarchy."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.ui_chat import detect_prompt_locale
from serenity_twin.ui_render import (
    _parse_thesis_bullets,
    build_structured,
    render_agent_slot,
    render_html,
    render_llm_markdown,
)


SIVE_SNIPPET = """### SIVE / SIVEF — CW/DFB merchant laser
- **Thesis:** Primary pure-play merchant DFB/CW laser supplier.
- **Key evidence:** +73.78% single day after CPO cheat sheet. May 25 update adds Jabil evidence. June 2 follow-up quotes Sivers laser arrays. June 3 reply adds NVDA catalyst.
- **Latest stance (May 2026):** Core position, no exit signal.
"""


def test_key_evidence_splits_into_timeline():
    items = _parse_thesis_bullets(SIVE_SNIPPET)
    evidence = next(i for i in items if i["label"] == "Key evidence")
    assert len(evidence.get("subitems", [])) >= 3
    assert evidence.get("tier") == "detail"


def test_thesis_primary_labels_sorted_first():
    items = _parse_thesis_bullets(SIVE_SNIPPET)
    labels = [i["label"] for i in items]
    assert labels.index("Thesis") < labels.index("Key evidence")


def test_detect_prompt_locale_english():
    assert detect_prompt_locale("What is Serenity's view on $SIVE?", "zh") == "en"


def test_detect_prompt_locale_chinese():
    assert detect_prompt_locale("总结 $SIVE 观点", "en") == "zh"


def test_references_collapsed_below_support():
    ctx = {
        "ticker": "SIVE",
        "lookup": {
            "found_in_theses": True,
            "thesis": {"sector": "Optical", "file": "theses/x.md", "markdown": SIVE_SNIPPET},
            "recent_tweets": [{"created_at": "2026-06-01", "kind": "post", "url": "https://x.com/a", "text_preview": "tweet"}],
        },
        "live_web": {
            "quote": {"status": "ok", "regular_market_price": 78.8, "currency": "SEK", "change_pct_1d": 1.2},
            "news_search": [{"title": "News", "url": "https://example.com", "snippet": "snip"}],
        },
    }
    s = build_structured(ctx, "A", "en", suppress_synthesis=True)
    types = [sec.get("type") for sec in s["sections"]]
    assert "collapsible" in types
    ref = next(sec for sec in s["sections"] if sec.get("type") == "collapsible")
    assert ref.get("default_open") is False
    inner_types = [c.get("type") for c in ref.get("sections", [])]
    assert "tweets" in inner_types or "sources" in inner_types


def test_agent_slot_prepended_in_report():
    slot = render_agent_slot("en", hidden=False)
    html = slot + render_html(build_structured({"ticker": "SIVE", "lookup": {}, "live_web": {}}, "A", "en"))
    assert "agent-hero" in html
    assert html.index("agent-hero") < html.index("report-header") or "agent-hero" in html[:400]


def test_render_llm_markdown_bullets():
    md = "## Serenity view\n\n- Highest conviction CPO laser play\n- No exit signal"
    html = render_llm_markdown(md)
    assert "agent-md-h3" in html
    assert "<li>" in html
    assert "<strong>" not in html or "Highest" in html
