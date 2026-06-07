#!/usr/bin/env python3
"""End-to-end quality control for serenity-twin."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.paths import (
    LEGACY_TWEETS_JSON,
    MENTIONS_EVENTS_CSV,
    THESIS_INDEX,
    TWEETS_JSON,
)
from serenity_twin.theses_index import load_index
from serenity_twin.tweets import load_archive

EVALS = ROOT / "evals" / "ticker-lookup.yaml"


def run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out.strip()


def main() -> None:
    errors: list[str] = []
    checks: list[str] = []

    ok, out = run([sys.executable, "scripts/validate_skill.py", "."])
    checks.append(f"validate_skill: {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(out)

    if LEGACY_TWEETS_JSON.exists():
        errors.append(f"Legacy file still present: {LEGACY_TWEETS_JSON.name}")

    if not TWEETS_JSON.exists():
        errors.append("Missing corpus/data/tweets.json")
    else:
        rows = load_archive(TWEETS_JSON)
        checks.append(f"tweets.json: {len(rows)} records (canonical schema)")
        if rows:
            sample = rows[0]
            for key in ("id", "text", "created_at", "url", "kind", "tickers", "metrics"):
                if key not in sample:
                    errors.append(f"Canonical schema missing field: {key}")

    if not THESIS_INDEX.exists():
        errors.append("Missing theses-index.json — run scripts/split_theses.py")
    else:
        idx = load_index()
        n = len(idx.get("tickers", {}))
        checks.append(f"theses-index.json: {n} tickers")

    ok, out = run([sys.executable, "scripts/rebuild_mentions.py"])
    checks.append(f"rebuild_mentions: {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(out)
    elif not MENTIONS_EVENTS_CSV.exists():
        errors.append("mentions-events.csv not created")

    ok, out = run([sys.executable, "scripts/radar.py", "--json", "--top", "3"])
    checks.append(f"radar: {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(out)
    else:
        try:
            data = json.loads(out)
            if "heating" not in data:
                errors.append("radar JSON missing heating block")
        except json.JSONDecodeError:
            errors.append("radar --json invalid JSON")

    ok, out = run([sys.executable, "scripts/lookup_ticker.py", "SIVE", "--json", "--no-radar"])
    checks.append(f"lookup_ticker SIVE: {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(out or "SIVE not found")

    ok, out = run([sys.executable, "scripts/distill_candidates.py"])
    checks.append(f"distill_candidates: {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(out)

    if EVALS.exists():
        ok, out = run([sys.executable, "-m", "pytest", "tests/test_evals.py", "-q"])
        checks.append(f"evals: {'OK' if ok else 'FAIL'}")
        if not ok:
            errors.append(out)

    report = {"checks": checks, "errors": errors, "status": "PASS" if not errors else "FAIL"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
