"""Configuration and optional X API credentials."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from serenity_twin.paths import ROOT

ENV_FILE = ROOT / ".env"
CONFIG_FILE = ROOT / "config.json"

DEFAULT_HANDLE = "aleabitoreddit"
DEFAULT_DISPLAY = "Serenity"


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class Settings:
    handle: str = DEFAULT_HANDLE
    display_name: str = DEFAULT_DISPLAY
    lookback_hours: int = 36
    max_tweets: int = 100
    x_bearer_token: str | None = None
    twitter_sync_enabled: bool = False
    allow_syndication_fallback: bool = False

    @classmethod
    def load(cls) -> "Settings":
        file_env = _load_dotenv(ENV_FILE)
        merged = {**file_env, **{k: v for k, v in os.environ.items() if k.startswith("X_") or k.startswith("SERENITY_")}}
        cfg = _load_json(CONFIG_FILE)

        token = merged.get("X_BEARER_TOKEN") or merged.get("SERENITY_X_BEARER_TOKEN")
        synd = merged.get("SERENITY_SYNDICATION_FALLBACK", cfg.get("allow_syndication_fallback", False))
        allow_syndication = str(synd).lower() in {"1", "true", "yes", "on"}
        explicit = merged.get("SERENITY_TWITTER_SYNC_ENABLED", cfg.get("twitter_sync_enabled"))
        if explicit is not None:
            sync_enabled = str(explicit).lower() in {"1", "true", "yes", "on"}
        else:
            sync_enabled = bool(token) or allow_syndication

        return cls(
            handle=cfg.get("handle", DEFAULT_HANDLE),
            display_name=cfg.get("display_name", DEFAULT_DISPLAY),
            lookback_hours=int(cfg.get("lookback_hours", 36)),
            max_tweets=int(cfg.get("max_tweets", 100)),
            x_bearer_token=token,
            twitter_sync_enabled=sync_enabled and bool(token or allow_syndication),
            allow_syndication_fallback=allow_syndication,
        )

    def sync_status_message(self) -> str:
        if self.twitter_sync_enabled and self.x_bearer_token:
            return "Twitter sync enabled (X API)."
        if self.twitter_sync_enabled and self.allow_syndication_fallback:
            return "Twitter sync enabled (syndication fallback only)."
        if not self.x_bearer_token and not self.allow_syndication_fallback:
            return (
                "Twitter sync disabled: no X_BEARER_TOKEN and syndication fallback off. "
                "Using bundled corpus."
            )
        return "Twitter sync disabled by config."
