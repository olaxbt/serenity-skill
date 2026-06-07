# Quick start — new clone

Run **one command** in Cursor terminal from `serenity-twin/`:

```bash
python aio_serenity.py
```

This will:

1. **Auto-init** on first run (`init_system.py` — corpus, theses, mentions, QC, Cursor skill, `.env`)
2. **Open the browser UI** (default http://127.0.0.1:17876 — if busy, next free port is picked automatically)

You do **not** run `lookup_ticker.py` or `live_research.py` yourself — the UI runs them on every prompt.

---

## Other commands (optional)

```bash
python aio_serenity.py --init          # init only, no browser
python aio_serenity.py --no-browser    # UI without opening a tab
python aio_serenity.py --port 3000     # use a specific port
python aio_serenity.py --strict-port   # fail if --port is taken (no auto-fallback)
python scripts/init_system.py          # same as --init (explicit)
```

## Cursor Chat (alternative to browser)

After init once, use **Agent** chat in Cursor (no terminal per question):

```text
用 serenity-twin：Serenity 对 $SIVE 怎么看？
```

The Agent should auto-run `live_research.py` + `lookup_ticker.py` — you never type those.

## Optional keys (`.env`)

| Variable | Purpose |
|----------|---------|
| `DEEPSEEK_API_KEY` | Browser UI LLM synthesis |
| `X_BEARER_TOKEN` | Live tweet sync |

Cursor chat: configure DeepSeek in **Cursor Settings → Models**.

## Optional — daily refresh (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/daily_brief.ps1
```

## Optional — dev tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -q
```
