"""Shared markdown → HTML for agent narrative (browser UI)."""

from __future__ import annotations

import html
import re


def render_agent_markdown(text: str) -> str:
    """Lightweight markdown → HTML for agent answers (no external deps)."""
    if not text:
        return ""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(s: str) -> str:
        s = html.escape(s, quote=True)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        return s

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_lists()
            continue
        if line.startswith("### "):
            close_lists()
            out.append(f'<h4 class="agent-md-h4">{inline(line[4:].strip())}</h4>')
        elif line.startswith("## "):
            close_lists()
            out.append(f'<h3 class="agent-md-h3">{inline(line[3:].strip())}</h3>')
        elif line.startswith("# "):
            close_lists()
            out.append(f'<h3 class="agent-md-h3">{inline(line[2:].strip())}</h3>')
        elif line.startswith("> "):
            close_lists()
            out.append(f'<blockquote class="agent-blockquote">{inline(line[2:].strip())}</blockquote>')
        elif re.match(r"^[-*]\s+", line):
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append('<ul class="agent-md-list">')
                in_ul = True
            bullet = re.sub(r"^[-*]\s+", "", line)
            out.append(f"<li>{inline(bullet)}</li>")
        elif re.match(r"^\d+\.\s+", line):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append('<ol class="agent-md-ol">')
                in_ol = True
            item = re.sub(r"^\d+\.\s+", "", line)
            out.append(f"<li>{inline(item)}</li>")
        else:
            close_lists()
            out.append(f'<p class="agent-md-p">{inline(line)}</p>')
    close_lists()
    return "".join(out)


# Back-compat alias used by ui_render
render_llm_markdown = render_agent_markdown
