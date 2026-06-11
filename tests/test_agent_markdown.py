"""Agent markdown rendering."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.agent_markdown import render_agent_markdown


def test_render_sections_and_bullets():
    md = "## Executive summary\n\nTheme scan for AI semis.\n\n## Scarce layers\n\n- CoWoS packaging\n- HBM"
    html = render_agent_markdown(md)
    assert 'class="agent-md-h3"' in html
    assert "<li>" in html
    assert "CoWoS" in html


def test_render_ordered_list_and_blockquote():
    md = "## Next steps\n\n1. Rank layers\n2. Cross-check corpus\n\n> *research map* only"
    html = render_agent_markdown(md)
    assert 'class="agent-md-ol"' in html
    assert 'class="agent-blockquote"' in html
    assert "<em>research map</em>" in html
