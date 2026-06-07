"""Optional DeepSeek API for automated thesis distillation."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from serenity_twin.paths import ROOT

ENV_FILE = ROOT / ".env"


def load_deepseek_key() -> str | None:
    key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("SERENITY_DEEPSEEK_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def summarize_thesis_delta(
    ticker: str,
    tweet_text: str,
    current_section: str,
    *,
    api_key: str | None = None,
) -> str | None:
    """Return a one-paragraph Latest stance delta, or None if API unavailable."""
    api_key = api_key or load_deepseek_key()
    if not api_key:
        return None

    prompt = f"""You maintain Serenity (@aleabitoreddit) thesis files. Given a new tweet and the existing thesis section for ${ticker}, write ONE compact bullet for "**Latest stance (auto-distilled YYYY-MM-DD):**" format.

Rules (from maintenance playbook):
- Only durable stance/catalyst/invalidation changes
- Compact, no hype, cite the signal not long quotes
- If tweet is low-signal reply/joke, respond with exactly: SKIP
- Max 3 sentences

Existing section (truncated):
{current_section[:3000]}

New tweet:
{tweet_text[:2000]}

Output only the bullet line content after the date label, or SKIP."""

    body = json.dumps(
        {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 400,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        if content.upper() == "SKIP" or not content:
            return None
        return content
    except Exception:
        return None
