#!/usr/bin/env python3
"""Deprecated wrapper — use aio_serenity.py at repo root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raise SystemExit(
    subprocess.call(
        [sys.executable, str(ROOT / "aio_serenity.py"), *sys.argv[1:]],
        cwd=str(ROOT),
    )
)
