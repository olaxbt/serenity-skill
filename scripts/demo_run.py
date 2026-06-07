#!/usr/bin/env python3
"""Demo: full offline pipeline for serenity-twin."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ["python", "scripts/validate_skill.py", "."],
    ["python", "scripts/normalize_corpus.py"],
    ["python", "scripts/split_theses.py"],
    ["python", "scripts/rebuild_mentions.py"],
    ["python", "scripts/radar.py", "--window", "14", "--top", "5"],
    ["python", "scripts/lookup_ticker.py", "SIVE", "--json", "--no-radar"],
    ["python", "scripts/distill_candidates.py"],
    ["python", "scripts/run_qc.py"],
]


def main() -> None:
    env = {**dict(__import__("os").environ), "PYTHONIOENCODING": "utf-8"}
    for step in STEPS:
        print("\n>>>", " ".join(step))
        proc = subprocess.run(step, cwd=str(ROOT), env=env)
        if proc.returncode != 0:
            raise SystemExit(proc.returncode)
    print("\nDEMO OK")


if __name__ == "__main__":
    main()
