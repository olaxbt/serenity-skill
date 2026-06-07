#!/usr/bin/env python3
"""Agent-automated distillation: classify new tweets and apply corpus updates."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.distill import classify_tweet
from serenity_twin.distill_apply import apply_candidates
from serenity_twin.paths import DISTILL_CANDIDATES, DISTILL_STATE, TWEETS_JSON
from serenity_twin.tweets import load_archive


def load_state() -> dict:
    if not DISTILL_STATE.exists():
        return {"processed_ids": []}
    return json.loads(DISTILL_STATE.read_text(encoding="utf-8"))


def save_state(processed_ids: set[str]) -> None:
    DISTILL_STATE.parent.mkdir(parents=True, exist_ok=True)
    DISTILL_STATE.write_text(
        json.dumps({"processed_ids": sorted(processed_ids)[-10000:]}, indent=2) + "\n",
        encoding="utf-8",
    )


def collect_new_tweets() -> list[dict]:
    state = load_state()
    processed = set(state.get("processed_ids") or [])
    archive = load_archive(TWEETS_JSON)
    return [t for t in archive if t["id"] not in processed]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-automated distill apply")
    parser.add_argument("--since-sync", action="store_true", help="Only tweets not in distill-state")
    parser.add_argument("--no-llm", action="store_true", help="Skip DeepSeek summarization")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    new_tweets = collect_new_tweets() if args.since_sync else load_archive(TWEETS_JSON)
    candidates = [classify_tweet(t) for t in new_tweets]
    actionable = [c for c in candidates if c["category"] not in {"skip", "data-only"}]

    if args.dry_run:
        print(json.dumps({"actionable": len(actionable), "sample": actionable[:3]}, indent=2))
        return

    stats = apply_candidates(actionable, use_llm=not args.no_llm)
    processed = set(load_state().get("processed_ids") or [])
    processed.update(t["id"] for t in new_tweets)
    save_state(processed)

    DISTILL_CANDIDATES.write_text(
        json.dumps({"candidates": candidates, "applied_stats": stats}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"applied": stats, "processed": len(new_tweets)}, indent=2))

    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_qc.py")], cwd=str(ROOT), check=False)


if __name__ == "__main__":
    main()
