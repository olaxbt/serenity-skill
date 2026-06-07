# Contributing

## What we welcome

- Corpus updates from new Serenity posts (follow `distillation/MAINTENANCE.md`)
- Bug fixes in Python scripts
- Documentation and example prompts
- Tests for `serenity_twin/` utilities and radar math

## What we do not accept

- Buy/sell signals or trading automation
- Full text redistribution of X Articles or paywalled content
- Commits that add `.env` or API keys

## Distillation workflow

1. `python scripts/sync_tweets.py` (if X token configured)
2. Classify new posts per `distillation/MAINTENANCE.md`
3. Update `corpus/references/theses.md` or `track-record.md` with the smallest useful edit
4. Run `python scripts/rebuild_mentions.py`

## Pull request checklist

- [ ] No secrets in diff
- [ ] `python scripts/validate_skill.py .` passes
- [ ] Stated whether corpus or code changed
- [ ] Disclaimer preserved for investment-related output
