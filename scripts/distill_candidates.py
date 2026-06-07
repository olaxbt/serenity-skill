#!/usr/bin/env python3
"""Classify new tweets since last run for thesis/track-record distillation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.distill import classify_tweet
from serenity_twin.paths import DISTILL_CANDIDATES, DISTILL_STATE, TWEETS_JSON
from serenity_twin.tweets import load_archive

SKIP_CATEGORIES = {"skip", "data-only"}


def load_state() -> dict:
    if not DISTILL_STATE.exists():
        return {"processed_ids": [], "last_run": None}
    return json.loads(DISTILL_STATE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    DISTILL_STATE.parent.mkdir(parents=True, exist_ok=True)
    DISTILL_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill candidates from new tweets")
    parser.add_argument("--since-id", default=None, help="Only tweets newer than this id (optional)")
    parser.add_argument("--mark-processed", action="store_true", help="Update distill-state.json after run")
    parser.add_argument("--all-new", action="store_true", help="Ignore state; classify tweets not in state")
    args = parser.parse_args()

    if not TWEETS_JSON.exists():
        raise SystemExit(f"Missing {TWEETS_JSON}")

    archive = load_archive(TWEETS_JSON)
    state = load_state()
    processed = set(state.get("processed_ids") or [])

    new_tweets = []
    for t in archive:
        tid = t["id"]
        if args.since_id and tid <= args.since_id:
            continue
        if not args.all_new and tid in processed:
            continue
        new_tweets.append(t)

    candidates = [classify_tweet(t) for t in new_tweets]
    actionable = [c for c in candidates if c["category"] not in SKIP_CATEGORIES]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "new_tweet_count": len(new_tweets),
        "actionable_count": len(actionable),
        "candidates": candidates,
        "summary_by_category": {},
        "next_steps": [
            "Review actionable candidates in data/distill-candidates.json",
            "Apply updates per distillation/MAINTENANCE.md",
            "Re-run scripts/split_theses.py if sector thesis files changed",
            "Re-run scripts/run_qc.py",
        ],
        "learning_loop_note": (
            "X API sync updates tweets.json automatically. This script closes the loop to "
            "actionable distillation tasks; agent/human still applies edits to theses/track-record."
        ),
    }
    for c in candidates:
        cat = c["category"]
        payload["summary_by_category"][cat] = payload["summary_by_category"].get(cat, 0) + 1

    DISTILL_CANDIDATES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"new": len(new_tweets), "actionable": len(actionable), "path": str(DISTILL_CANDIDATES)}, indent=2))

    if args.mark_processed and new_tweets:
        processed.update(t["id"] for t in new_tweets)
        state["processed_ids"] = sorted(processed)[-10000:]
        state["last_run"] = payload["generated_at"]
        save_state(state)


if __name__ == "__main__":
    main()
