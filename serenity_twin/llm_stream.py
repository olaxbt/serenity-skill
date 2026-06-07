"""Streaming DeepSeek chat completions (stdlib)."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator
from typing import Any

from serenity_twin.agent_prompt import build_agent_system_prompt
from serenity_twin.llm import load_deepseek_key


def stream_chat_completion(
    prompt: str,
    context: dict[str, Any],
    *,
    api_key: str | None = None,
) -> Iterator[str]:
    api_key = api_key or load_deepseek_key()
    if not api_key:
        return
        yield  # pragma: no cover — makes this a generator when no key

    from serenity_twin.ui_chat import detect_prompt_locale

    mode = context.get("mode", "A")
    answer_locale = detect_prompt_locale(prompt, context.get("locale", "en"))
    system = build_agent_system_prompt(mode, locale=answer_locale)
    user_content = (
        f"User prompt:\n{prompt}\n\n"
        f"Required answer language: {'Chinese' if answer_locale == 'zh' else 'English'}\n\n"
        f"Executed script context (authoritative — do not invent beyond this):\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)[:18000]}"
    )
    body = json.dumps(
        {
            "model": "deepseek-chat",
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "max_tokens": 4096 if mode in ("C", "D") else 2500,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk["choices"][0].get("delta", {})
                text = delta.get("content")
                if text:
                    yield text
            except (json.JSONDecodeError, KeyError, IndexError):
                continue


def chat_completion_sync(prompt: str, context: dict[str, Any], *, api_key: str | None = None) -> str:
    parts = list(stream_chat_completion(prompt, context, api_key=api_key))
    return "".join(parts) if parts else ""
