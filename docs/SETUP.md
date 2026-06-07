# Production setup — Cursor (local) vs OpenClaw (community)

## Where is the chat UI?

This repo is an **Agent Skill**, not a standalone web app. There is **no built-in Serenity chat UI**.

| Runtime | How you talk to Serenity Twin |
|---------|------------------------------|
| **Cursor (your setup)** | **Cursor Chat panel** (UI) — type prompts in the IDE |
| **OpenClaw (community)** | OpenClaw CLI, TUI, or Telegram/Discord/etc. gateway |
| **Neither** | No chat — scripts only (`lookup_ticker.py`, `radar.py`) |

You converse with the **LLM inside your agent client**. The skill provides corpus + workflows.

---

## One-command init (production)

From repo root:

```bash
python scripts/init_system.py
```

This runs: validate → normalize corpus → split theses → rebuild mentions → QC PASS.

Optional dev tests:

```bash
pip install -r requirements-dev.txt
pytest tests/ -q
```

---

## API keys — where to put them

### DeepSeek (LLM for chat) — **Cursor UI, not terminal**

**Recommended for Cursor users:**

1. Open **Cursor Settings → Models**
2. Add **DeepSeek** and paste your API key there
3. Select DeepSeek as the chat/agent model

The skill does **not** read `DEEPSEEK_API_KEY` for normal chat. Cursor passes the model to the agent automatically.

### DeepSeek in `.env` — **optional, scripts only**

Put `DEEPSEEK_API_KEY` in `.env` **only if** you want headless thesis auto-distillation:

```bash
python scripts/agent_distill.py --since-sync
```

Without it, auto-distill still runs but appends tweet preview stubs instead of LLM-polished stance bullets.

### X API (tweet sync) — **`.env` file**

```bash
cp .env.example .env
# Edit .env:
X_BEARER_TOKEN=your_token
```

Enable in `config.json`:

```json
{ "twitter_sync_enabled": true }
```

Then:

```bash
python scripts/sync_tweets.py --include-replies --distill
python scripts/agent_distill.py --since-sync
python scripts/rebuild_mentions.py
```

---

## Cursor vs OpenClaw — recommendation

| | **Cursor (you)** | **OpenClaw (community)** |
|--|------------------|--------------------------|
| Install skill | `.cursor/skills/serenity-twin/` via `install-cursor-skill.ps1` | `~/.hermes/skills/research/serenity-twin/` or external skill dir |
| DeepSeek key | **Cursor Settings UI** | OpenClaw model config |
| Chat UI | Cursor Chat | OpenClaw TUI / messaging |
| Best for | Deep research sessions, editing theses | 24/7 cron, Telegram briefs |

**Suggest:** publish repo as Agent Skill compatible with both; document both paths. You use **Cursor + DeepSeek via UI**; community uses **OpenClaw + their model provider**.

---

## Automated thesis write-back (agent, not manual)

After tweet sync, run:

```bash
python scripts/agent_distill.py --since-sync
```

This **automatically**:

1. Classifies new tweets
2. Appends **track-record** rows
3. Appends **Latest stance (auto-distilled)** bullets to sector thesis files
4. Refreshes `theses-index.json` (uses DeepSeek in `.env` if set for cleaner bullets)
5. Runs QC

In Cursor, you can also say:

```text
运行 serenity-twin 同步后自动蒸馏：sync_tweets → agent_distill → rebuild_mentions
```

The agent executes the same scripts — no manual file editing.

---

## Daily production loop (with X API)

```bash
python scripts/sync_tweets.py --include-replies
python scripts/agent_distill.py --since-sync
python scripts/rebuild_mentions.py
python scripts/radar.py --window 14
```

Then chat in Cursor:

```text
用 serenity-twin：总结今天 radar Heating 的 ticker 和她的最新观点。
```

---

## Browser UI (prototype)

After init, launch a local web UI to try sample prompts (scripts run server-side):

```bash
python aio_serenity.py
```

Opens `http://127.0.0.1:17876/` by default. If that port is taken, the next free port is used (see terminal output). Override with `--port 3000`.

- **Without** `DEEPSEEK_API_KEY`: Mode A/B/C/D still run **auto live web** (Yahoo quote + DuckDuckGo news + SEC) plus corpus scripts.
- **With** `DEEPSEEK_API_KEY` in `.env`: LLM synthesizes corpus + live web into narrative answers.
- No need to type “search internet” — live fetch is automatic on every analysis prompt.

---

## Daily brief (Windows Task Scheduler)

Refresh corpus + write a radar snapshot without opening Cursor:

```powershell
cd serenity-twin
powershell -ExecutionPolicy Bypass -File scripts/daily_brief.ps1
```

Outputs:

- `corpus/data/daily-brief-latest.txt` — paste into chat or read in Agent
- `corpus/data/daily-brief-YYYY-MM-DD.txt` — dated archive
- `corpus/data/daily-brief.log` — run log

**Register daily run (optional):** Task Scheduler → Create Task → Trigger 07:00 → Action:

```text
powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\serenity-twin\scripts\daily_brief.ps1"
```

Sample prompts after cron: see `docs/sample_prompts.md` (Daily brief section).

Cloud alternative: `.github/workflows/weekly-sync.yml` (needs `X_BEARER_TOKEN` secret on GitHub).
