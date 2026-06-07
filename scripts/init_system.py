#!/usr/bin/env python3
"""One-command production initialization for serenity-twin."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Validate skill", [sys.executable, "scripts/validate_skill.py", "."]),
    ("Normalize tweet corpus", [sys.executable, "scripts/normalize_corpus.py"]),
    ("Split theses index", [sys.executable, "scripts/split_theses.py"]),
    ("Rebuild mentions", [sys.executable, "scripts/rebuild_mentions.py"]),
    ("Quality control", [sys.executable, "scripts/run_qc.py"]),
]


def main() -> None:
    env_example = ROOT / ".env.example"
    env_file = ROOT / ".env"
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Created {env_file} from .env.example — edit X_BEARER_TOKEN if needed.")

    cursor_skill = ROOT / ".cursor" / "skills" / "serenity-twin"
    if not (cursor_skill / "SKILL.md").exists():
        ps1 = ROOT / "install-cursor-skill.ps1"
        if ps1.exists() and sys.platform == "win32":
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)], cwd=str(ROOT), check=False)

    for label, cmd in STEPS:
        print(f"\n>>> {label}")
        proc = subprocess.run(cmd, cwd=str(ROOT), env={**dict(__import__("os").environ), "PYTHONIOENCODING": "utf-8"})
        if proc.returncode != 0:
            raise SystemExit(f"Init failed at: {label}")

    # Seed distill state so agent_distill --since-sync only processes future tweets
    sys.path.insert(0, str(ROOT))
    from serenity_twin.paths import DISTILL_STATE, TWEETS_JSON
    from serenity_twin.tweets import load_archive
    import json

    archive = load_archive(TWEETS_JSON)
    DISTILL_STATE.parent.mkdir(parents=True, exist_ok=True)
    DISTILL_STATE.write_text(
        json.dumps({"processed_ids": [t["id"] for t in archive]}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nSeeded distill-state with {len(archive)} tweet ids (future sync only).")

    print("\n" + "=" * 60)
    print("INIT OK — start the agent:")
    print("  python aio_serenity.py")
    print("\nOr Cursor chat (Agent mode):")
    print('  用 serenity-twin：Serenity 对 $SIVE 怎么看？')
    print("\nDeepSeek: Cursor Settings → Models, or .env DEEPSEEK_API_KEY for browser UI")
    print("X API (optional): edit .env → X_BEARER_TOKEN")
    print("=" * 60)


if __name__ == "__main__":
    main()
