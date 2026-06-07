#!/usr/bin/env python3
"""Serenity attention radar from mention events CSV."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serenity_twin.csv_util import read_csv
from serenity_twin.paths import MENTIONS_EVENTS_CSV
from serenity_twin.themes import theme_of


def _day_diff(asof: str, event_date: str) -> int:
    a = datetime.fromisoformat(asof + "T00:00:00+00:00")
    b = datetime.fromisoformat(event_date + "T00:00:00+00:00")
    return (a - b).days


def compute_radar(events: list[dict[str, str]], asof: str, window: int, top: int) -> dict:
    stat: dict[str, dict] = {}
    for event in events:
        event_date = (event.get("created_at") or "")[:10]
        if not event_date:
            continue
        d = _day_diff(asof, event_date)
        if d < 0:
            continue
        tickers = [t for t in (event.get("tickers") or "").split("|") if t]
        text = event.get("text") or ""
        for ticker in set(tickers):
            if ticker not in stat:
                stat[ticker] = {
                    "ticker": ticker,
                    "total": 0,
                    "recent": 0,
                    "prev": 0,
                    "first": event_date,
                    "last": event_date,
                }
            s = stat[ticker]
            s["total"] += 1
            if event_date < s["first"]:
                s["first"] = event_date
            if event_date > s["last"]:
                s["last"] = event_date
            if d < window:
                s["recent"] += 1
            elif d < 2 * window:
                s["prev"] += 1

    rows = []
    for s in stat.values():
        rows.append(
            {
                **s,
                "velocity": s["recent"] - s["prev"],
                "age_days": _day_diff(asof, s["first"]),
                "recency_days": _day_diff(asof, s["last"]),
            }
        )

    heating = sorted(
        [r for r in rows if r["recent"] >= 2 and r["velocity"] > 0],
        key=lambda r: (-r["velocity"], -r["recent"]),
    )[:top]

    fresh = sorted(
        [r for r in rows if r["age_days"] <= window and r["recent"] >= 2],
        key=lambda r: (-r["recent"], r["age_days"]),
    )[:top]

    conviction = sorted(
        [r for r in rows if r["recent"] >= 4 and r["recency_days"] <= (window + 1) // 2 and r["age_days"] >= window],
        key=lambda r: -r["recent"],
    )[:top]

    theme_recent: dict[str, int] = {}
    theme_prev: dict[str, int] = {}
    for event in events:
        event_date = (event.get("created_at") or "")[:10]
        if not event_date:
            continue
        d = _day_diff(asof, event_date)
        if d < 0 or d >= 2 * window:
            continue
        bucket = theme_recent if d < window else theme_prev
        tickers = [t for t in (event.get("tickers") or "").split("|") if t]
        themes = {theme_of(t, event.get("text") or "") for t in tickers} or {theme_of("", event.get("text") or "")}
        for th in themes:
            bucket[th] = bucket.get(th, 0) + 1

    all_themes = set(theme_recent) | set(theme_prev)
    theme_rotation = sorted(
        [
            {
                "theme": th,
                "recent": theme_recent.get(th, 0),
                "prev": theme_prev.get(th, 0),
                "delta": theme_recent.get(th, 0) - theme_prev.get(th, 0),
            }
            for th in all_themes
        ],
        key=lambda t: -t["recent"],
    )

    return {
        "asof": asof,
        "window_days": window,
        "heating": [
            {"ticker": s["ticker"], "recent": s["recent"], "prev": s["prev"], "velocity": s["velocity"], "total": s["total"], "last": s["last"]}
            for s in heating
        ],
        "new_entrants": [
            {"ticker": s["ticker"], "recent": s["recent"], "first_seen": s["first"], "age_days": s["age_days"]}
            for s in fresh
        ],
        "conviction_watch": [
            {"ticker": s["ticker"], "recent": s["recent"], "total": s["total"], "active_days": s["age_days"]}
            for s in conviction
        ],
        "theme_rotation": theme_rotation,
    }


def format_text(result: dict) -> str:
    w = result["window_days"]
    lines = [f"# Serenity radar — asof {result['asof']}, window {w}d (recent {w}d vs prior {w}d)", ""]
    lines.append("## Heating (attention momentum)")
    for row in result["heating"]:
        lines.append(f"ticker={row['ticker']}  delta={row['velocity']}  recent={row['recent']}  prev={row['prev']}")
    if not result["heating"]:
        lines.append("(none)")
    lines.append("")
    lines.append(f"## New entrants (first appeared within {w}d)")
    for row in result["new_entrants"]:
        lines.append(f"ticker={row['ticker']}  recent={row['recent']}  since={row['first_seen']}")
    if not result["new_entrants"]:
        lines.append("(none)")
    lines.append("")
    lines.append("## Conviction watch (repeated + still active)")
    for row in result["conviction_watch"]:
        lines.append(f"ticker={row['ticker']}  recent={row['recent']}  total={row['total']}")
    if not result["conviction_watch"]:
        lines.append("(none)")
    lines.append("")
    lines.append("## Theme rotation")
    for t in result["theme_rotation"]:
        arrow = "UP" if t["delta"] >= 0 else "DOWN"
        sign = "+" if t["delta"] >= 0 else ""
        lines.append(f"{arrow} {t['theme']}: {t['recent']} (was {t['prev']}, delta {sign}{t['delta']})")
    lines.append("")
    lines.append("— Candidate signals only. Cross-check corpus/references/theses.md. Not investment advice.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serenity attention radar")
    parser.add_argument("--events", type=Path, default=MENTIONS_EVENTS_CSV)
    parser.add_argument("--asof", default=None, help="YYYY-MM-DD")
    parser.add_argument("--window", type=int, default=14)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.events.exists():
        print(f"Events CSV not found: {args.events}", file=sys.stderr)
        print("Run: python scripts/rebuild_mentions.py", file=sys.stderr)
        raise SystemExit(1)

    events = read_csv(args.events)
    dates = sorted({(e.get("created_at") or "")[:10] for e in events if e.get("created_at")})
    asof = args.asof or (dates[-1] if dates else date.today().isoformat())
    result = compute_radar(events, asof, args.window, args.top)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
