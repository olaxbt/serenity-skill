# Sample prompts — Serenity Twin

Copy these into **Cursor Chat (Agent mode)** or any Agent Skills client. Prefix with `用 serenity-twin` so the skill loads.

> The agent **must** run bundled Python scripts before answering ticker/radar questions — you should not need to run scripts yourself after `init_system.py`. If the agent skips scripts, say: `先跑 lookup_ticker.py / radar.py，再回答。`

---

## Mode A — Ticker view（她对某只股怎么看）

**When:** One ticker, conviction, evolution, risks.

```text
用 serenity-twin：Serenity 对 $SIVE 的看法是什么？先跑 lookup_ticker.py --json，给出 conviction tier、演变时间线和主要风险。
```

```text
用 serenity-twin：$AXTI 在 InP 产业链里卡在哪一层？corpus latest stance 是否 stale？
```

```text
用 serenity-twin：比较 $SIVE、$LITE、$AAOI，按 Serenity lens 谁更值得优先研究？
```

```text
用 serenity-twin：$IREN 有没有 reversal？查 theses + track-record。
```

```text
用 serenity-twin：Serenity 从未深度覆盖的 $NVTS，用 methodology checklist 做 fresh-name 分析。
```

```text
What is Serenity's view on $POET? Run lookup_ticker.py first, then five-section output (中文).
```

---

## Mode B — Radar（注意力 / 她在 ramp 什么）

**When:** Attention momentum, heating tickers, theme rotation.

```text
用 serenity-twin：跑 radar.py（14 天），列出 Heating 和 New entrants，每个 cross-check lookup_ticker.py。
```

```text
用 serenity-twin：最近主题轮动是什么？compound semi / optical 是否在升温？
```

```text
用 serenity-twin：Conviction watch 里哪些在加热、哪些在降温？给 3 个最值得跟进的 ticker。
```

```text
用 serenity-twin：她最近在 ramp 什么？先 rebuild_mentions（如需要）再 radar。
```

---

## Mode C — Theme scan（产业链深度调研）

**When:** Broad theme → **rank scarce layers first**, then **stocks**; funds/ETF only when you ask.

**产业链** = value chain from end demand (e.g. hyperscaler capex) upstream through modules, chips, equipment, materials, infrastructure — find where supply is **scarce and hard to substitute** (Serenity's core lens).

Mode C is **not** “pick one fund.” It primarily screens **individual stocks** (US / A-share / HK). **Fund/ETF** is a **secondary output** when you explicitly want passive exposure — the agent checks whether ETF **top holdings** align with the scarce layers found in the chain.

```text
用 serenity-twin 深度调研 A 股 AI 半导体产业链：先排 scarce layer，再排 5–7 优先研究个股，最后给 ETF/基金方向（持仓是否对口瓶颈层）。
```

```text
用 serenity-twin：CPO/光通信主题 scan。按 deep-research-workflow：系统变化 → 产业链 8 层 → 稀缺层排序 → 公司候选 → 证据分级。
```

```text
用 serenity-twin：机器人产业链哪些环节接近真实瓶颈？A股/HK 可研究路径 + 下一步核查清单。
```

```text
用 serenity-twin：我想配置 AI 基建，不要直接荐基——先产业链筛个股，再说明哪些 ETF 持仓真正靠近卡点。
```

```text
用 serenity-twin：挑战 [公司名] 是不是蹭 AI 热点。用 Serenity 式产业链 + evidence ladder 分析。
```

```text
用 serenity-twin：US optical interconnect theme — rank layers, top 5 research names, cross-check Serenity theses for related tickers.
```

Optional scorecard:

```text
用 serenity-twin：对上面 top 3 候选跑 serenity_scorecard.py，输出 markdown 分数卡。
```

---

## Mode D — Research report（深度研报 / thesis memo）

**When:** Full memo structure, not a quick chat answer.

```text
用 serenity-twin：按 thesis-template.md 写 CPO/硅光产业链深度研报。区分 Serenity 语料观点 vs 独立核验 vs 研究地图。
```

```text
用 serenity-twin：写 $SIVE 单页 thesis memo：系统变化 → 卡点 → 证据阶梯 → 证伪条件 → next checks。
```

```text
用 serenity-twin：A 股 AI 半导体主题，输出完整研报（executive summary + 产业链 + 候选 + 风险），默认结论 tier 为「研究地图」除非证据足够。
```

---

## Mode E — Learning（对话式学她的方法）

**When:** Teach the method one step at a time; not a stock pick session.

Listed as **Learning** in `SKILL.md` (same as “Mode E” in docs).

```text
用 serenity-twin：带我学 Serenity 式产业链研究，从 AI capex 开始，每次只问我一个问题。
```

```text
用 serenity-twin：解释「卡点 investing」和 Mag7 customer filter，用 $AXTI 举例。
```

```text
用 serenity-twin：用五段式（她的观点 / 小白解释 / 第一性原理 / Buffett 判断 / 结论）分析 $XFAB，但重点是教方法不是荐股。
```

```text
用 serenity-twin：读 methodology.md 第 7 条原则，用 A 股一家设备公司举例怎么应用。
```

---

## Sync & freshness（有 X API 时）

```text
用 serenity-twin：执行完整同步链 sync_tweets --distill → agent_distill --since-sync → rebuild_mentions → radar，然后总结今天 Heating ticker。
```

```text
用 serenity-twin：sync 后告诉我 theses 和 track-record 有哪些自动更新。
```

---

## Daily brief（cron / 计划任务后）

After `scripts/daily_brief.ps1` or GitHub weekly sync, open the brief file or ask:

```text
用 serenity-twin：读 corpus/data/daily-brief-latest.txt，用中文总结今日 radar + 每条 Heating ticker 的 corpus 观点。
```

```text
用 serenity-twin：基于 daily brief，哪 2 个 ticker 最值得今天做 Mode D 短研报？
```

---

## Browser UI (prototype)

```bash
python aio_serenity.py
```

Opens http://127.0.0.1:17876 (or next free port) — click prompts from `ui/prompts.json`.

---

Same prompts work if the skill is installed and the runtime has **web/search tools** enabled for Mode C/D:

```text
serenity-twin: run lookup_ticker.py SIVE --json and answer in Chinese.
```

Configure web fetch in OpenClaw per your gateway; follow `reasoning/references/market-source-playbook.md` and `evidence-ladder.md` for source quality.

---

## Troubleshooting prompts

If answers feel like generic ChatGPT:

```text
用 serenity-twin：禁止臆测。必须先运行 python scripts/lookup_ticker.py TICKER --json，仅基于 JSON + corpus 文件回答。
```

```text
用 serenity-twin：声明当前是 bundled corpus 还是 live sync；若 thesis >60 天未更新且无新 tweet，标 ⚠️ stale。
```
