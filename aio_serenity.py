#!/usr/bin/env python3
"""
Serenity Twin — all-in-one entry point.

  python aio_serenity.py          # auto-init if needed, then open UI (interactive choice)
  python aio_serenity.py --init   # init only (corpus, QC, Cursor skill)
  python aio_serenity.py --open browser   # force system browser
  python aio_serenity.py --open cursor    # force Cursor Simple Browser
  python aio_serenity.py --no-browser     # server only, print URL

You do NOT run lookup_ticker / live_research manually — the UI and Cursor Agent
run them automatically on each prompt.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def is_initialized() -> bool:
    from serenity_twin.paths import MENTIONS_EVENTS_CSV, THESIS_INDEX, TWEETS_JSON

    return (
        THESIS_INDEX.exists()
        and MENTIONS_EVENTS_CSV.exists()
        and TWEETS_JSON.exists()
        and TWEETS_JSON.stat().st_size > 1000
    )


def run_init() -> None:
    script = ROOT / "scripts" / "init_system.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def choose_open_mode_interactive() -> str:
    print("\nWhere should Serenity Twin open?")
    print("  1) System browser (Chrome / Edge / …)  [default]")
    print("  2) Cursor IDE — Simple Browser (preview tab inside editor)")
    print("  3) Don't auto-open — copy URL from terminal")
    while True:
        try:
            choice = input("Choice [1]: ").strip().lower() or "1"
        except (EOFError, KeyboardInterrupt):
            print()
            return "none"
        if choice in ("1", "browser", "b", ""):
            return "browser"
        if choice in ("2", "cursor", "c"):
            return "cursor"
        if choice in ("3", "none", "n", "url"):
            return "none"
        print("Please enter 1, 2, or 3.")


def resolve_open_mode(args: argparse.Namespace) -> str:
    if args.no_browser:
        return "none"
    if args.open:
        return args.open
    if sys.stdin.isatty():
        return choose_open_mode_interactive()
    return "browser"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serenity Twin — init (if needed) + browser agent UI",
        epilog="Per-query scripts (lookup, live web) run inside the UI — not in your terminal.",
    )
    parser.add_argument("--init", action="store_true", help="Run init only, then exit")
    parser.add_argument("--no-init", action="store_true", help="Skip auto-init check")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port",
        type=int,
        default=17876,
        help="Preferred port (default 17876). If busy, tries the next free port.",
    )
    parser.add_argument(
        "--strict-port",
        action="store_true",
        help="Fail if --port is in use instead of auto-picking the next free port",
    )
    parser.add_argument(
        "--open",
        choices=["browser", "cursor", "none"],
        default=None,
        help="Where to open the UI (skips interactive prompt)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Same as --open none — server only",
    )
    args = parser.parse_args()

    if args.init or (not args.no_init and not is_initialized()):
        if not is_initialized():
            print("First run — initializing serenity-twin corpus and Cursor skill…")
        else:
            print("Running init (--init)…")
        run_init()
        if args.init:
            return

    from serenity_twin.ui_server import pick_port, serve

    port = args.port if args.strict_port else pick_port(args.host, args.port)
    if port != args.port:
        print(f"Port {args.port} is in use — using {port} instead.")

    open_mode = resolve_open_mode(args)
    print("\nSerenity Twin agent UI")
    print("Each prompt auto-runs: lookup_ticker + live_research + optional DeepSeek.\n")
    serve(host=args.host, port=port, open_mode=open_mode)


if __name__ == "__main__":
    main()
