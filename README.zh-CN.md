<div align="center">

<img src="docs/assets/readme-hero.png" alt="Serenity Skill — @aleabitoreddit 投研 Cursor Agent Skill（OlaXBT）" width="720" />

# Serenity Skill

**Serenity ([@aleabitoreddit](https://x.com/aleabitoreddit)) 投研 Agent Skill — 语料蒸馏、自动联网、注意力雷达与产业链瓶颈工作流**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](requirements.txt)
[![Agent Skill](https://img.shields.io/badge/Cursor%20Skill-SKILL.md-black)](SKILL.md)
[![Corpus](https://img.shields.io/badge/Tweets-5800%2B-green)](#语料库)
[![Tests](https://img.shields.io/badge/Tests-47%20passing-brightgreen)](#成熟度与质量评分)
[![UI](https://img.shields.io/badge/Browser%20UI-v0.3.10-e781fd)](#浏览器-agent-ui)

[演示视频](#演示视频) · [快速开始](#快速开始) · [架构](#架构) · [查询模式](#查询模式-ae) · [English](README.md)

</div>

---

## 演示视频

完整演示：单标的观点、实时行情、thesis 卡片与 Agent 叙述。

<p align="center">
  <video src="docs/assets/serenity-skill-demo.mp4" controls width="720" poster="docs/assets/readme-hero.png">
    <a href="docs/assets/serenity-skill-demo.mp4">下载演示视频</a>
  </video>
</p>

<p align="center"><sub>Serenity Skill 浏览器 UI · <code>python aio_serenity.py</code> · 仅作研究辅助</sub></p>

---

> **仅作研究辅助。** 提供研究优先级与推理，不构成投资建议，不执行交易。**与 @aleabitoreddit 无隶属关系。**

---

## 免责声明 — 研究蒸馏工具，非 Serenity 本人

**Serenity Skill** 是 **[OlaXBT](https://www.olaxbt.xyz) 独立开发的投研工具**，**不是** Serenity（[@aleabitoreddit](https://x.com/aleabitoreddit)）本人，**不代表**她的观点，也**不冒充**她。

| | |
|---|---|
| **是什么** | 将她**公开推文与文章**蒸馏为可查询语料 + 可联网的研究工作流 |
| **不是什么** | 她的实时观点、官方产品、投资建议或交易执行 |
| **如何阅读输出** | 区分 *语料观点* / *实时核验* / *研究地图* — 务必对照现价、新闻与 thesis 时效 |

---

## 一览

| | |
|---|---|
| **是什么** | **Serenity Skill** — Cursor/OpenClaw Agent Skill + Python 工具包 + 浏览器 UI |
| **核心问题** | *Serenity 对某 ticker 怎么看？该观点今天是否仍然成立？* |
| **一条命令** | `python aio_serenity.py` |
| **仓库** | [github.com/olaxbt/serenity-skill](https://github.com/olaxbt/serenity-skill) |
| **成熟度** | **8.9 / 10** |

---

## 能做什么

| 能力 | 示例 |
|------|------|
| **标的观点 (Mode A)** | *Serenity 对 $SIVE 怎么看？* |
| **注意力雷达 (Mode B)** | *14 天 radar + cross-check theses* |
| **产业链扫描 (Mode C)** | *A 股 AI 半导体 — 先 scarce layer，再个股* |
| **深度研报 (Mode D)** | *$SIVE thesis memo* |
| **学方法 (Mode E)** | *Serenity 式瓶颈投研，每次一问* |

完整 prompt：[`docs/sample_prompts.md`](docs/sample_prompts.md)

---

## 快速开始

```bash
git clone https://github.com/olaxbt/serenity-skill.git
cd serenity-skill
python aio_serenity.py
```

每个问题服务端自动跑 `lookup_ticker.py` + `live_research.py` + 结构化 HTML。

更多：[`docs/QUICKSTART.md`](docs/QUICKSTART.md)

---

## 三种使用方式

| 入口 | 适合 |
|------|------|
| **浏览器 UI** | 试 prompt、表格、价格图、中英 UI |
| **Cursor Chat** | Agent 模式 + `serenity-skill` |
| **OpenClaw** | 24/7 cron、Telegram |

---

## 查询模式 A–E

| 模式 | 触发 | 输出 |
|------|------|------|
| **A** | 单 ticker 观点 | 语料 + 实时核验 + Agent 叙述 |
| **B** | ramp / heating | 升温 / 新进 / 主题轮动表 |
| **C** | 产业链 / ETF | 先排层 → 个股 |
| **D** | 深度研报 | 完整 memo |
| **E** | 学方法 | 每次一问 |

---

## 浏览器 Agent UI

- 入口：`python aio_serenity.py` · **v0.3.10**
- 紫色主题 `#e781fd`，中/EN 切换
- Agent 步骤面板 + SSE 流式进度
- **OlaXBT 团队出品** — [官网](https://www.olaxbt.xyz) · [仓库](https://github.com/olaxbt/serenity-skill)

---

## 语料库

| 路径 | 内容 |
|------|------|
| `corpus/data/tweets.json` | **5826** 帖 |
| `corpus/references/theses/*.md` | **43** 条深度 thesis |
| `corpus/references/methodology.md` | 14 条原则 + checklist |

---

## 关键词与检索

**Serenity Skill**（[`olaxbt/serenity-skill`](https://github.com/olaxbt/serenity-skill)）是面向 **@aleabitoreddit（Serenity）** 粉丝的 open-source **Cursor Agent Skill** 与 **投研 Agent**。检索词：*serenity skill*、*aleabitoreddit 观点*、*Serenity 怎么看某 ticker*、*产业链卡点*、*CPO 半导体*、*Cursor 投研 skill*。

**能力：** 产业链卡点 · CPO/光通信/半导体 · 注意力 radar · A 股/美股主题扫描 · 深度研报 · 实时行情核验 · **Cursor IDE** · **浏览器 UI** · **OpenClaw**。[OlaXBT](https://www.olaxbt.xyz) 出品。

> 浏览器 UI 内部可能显示 “Serenity Twin” — 对外项目名称是 **Serenity Skill**（本仓库）。

---

## 来源与发布

整合自三个开源 Serenity skill 项目（详见英文 [Provenance](README.md#provenance)）。

**仅发布** [olaxbt/serenity-skill](https://github.com/olaxbt/serenity-skill)。

---

## 免责声明

- 自报收益未验证；thesis 会 decay  
- 社交帖仅为线索；高置信结论需公告/财报  
- 研究 lens，非信号源、非交易机器人  

---

## 许可证

[MIT](LICENSE)

---

<div align="center">

**[English README →](README.md)**

</div>
