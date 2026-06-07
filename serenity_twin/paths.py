"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus"
DATA = CORPUS / "data"
REFERENCES = CORPUS / "references"
THESIS_DIR = REFERENCES / "theses"
THESIS_INDEX = REFERENCES / "theses-index.json"
ANALYSIS = CORPUS / "analysis"
REASONING = ROOT / "reasoning"
DISTILLATION = ROOT / "distillation"
EVALS = ROOT / "evals"

TWEETS_JSON = DATA / "tweets.json"
TWEETS_CSV = DATA / "tweets.csv"
TICKER_STATS = DATA / "ticker_stats.txt"
MENTIONS_EVENTS_CSV = DATA / "mentions-events.csv"
MENTIONS_SUMMARY_CSV = DATA / "mentions-summary.csv"
DISTILL_STATE = DATA / "distill-state.json"
DISTILL_CANDIDATES = DATA / "distill-candidates.json"
MAINTENANCE = DISTILLATION / "MAINTENANCE.md"

# Legacy paths removed — do not recreate
LEGACY_TWEETS_JSON = DATA / "aleabitoreddit_tweets.json"
LEGACY_TWEETS_CSV = DATA / "aleabitoreddit_tweets.csv"
