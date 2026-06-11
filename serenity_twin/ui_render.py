"""Structured + HTML report rendering for the browser UI."""

from __future__ import annotations

import html
import re
from typing import Any

LABELS = {
    "en": {
        "ticker_lookup": "Ticker analysis",
        "corpus_thesis": "Serenity corpus thesis",
        "live_market": "Live market data",
        "recent_tweets": "Recent tweets",
        "web_sources": "Web sources",
        "radar": "Attention radar",
        "corpus_vs_live": "Corpus vs live market",
        "fresh_name": "Fresh name — not in corpus",
        "partial": "Partial coverage",
        "disclaimer": "Independent research distill — not Serenity, not investment advice.",
        "deep_thesis": "Deep thesis on file",
        "no_thesis": "No deep thesis in corpus",
        "price": "Price",
        "change_1d": "1D change",
        "range_52w": "52W range",
        "market_cap": "Market cap",
        "exchange": "Exchange",
        "instrument": "Instrument",
        "crypto_spot_note": "Crypto spot price via Yahoo (not an equity ETF).",
        "as_of": "As of",
        "signal": "Radar signal",
        "stale_hint": "Compare thesis date with live price/news. Flag stale if material change.",
        "metric": "Metric",
        "value": "Value",
        "source": "Source",
        "title": "Title",
        "date": "Date",
        "type": "Type",
        "velocity": "Velocity",
        "recent": "Recent",
        "ticker": "Ticker",
        "theme": "Theme",
        "delta": "Delta",
        "stale_title": "Thesis freshness",
        "stale_fresh": "Corpus stance is recent — still cross-check live data.",
        "stale_watch": "Corpus is aging — monitor price and news.",
        "stale_yes": "⚠️ Stale thesis — corpus date vs live price suggests re-verification.",
        "stale_soft": "⚠️ Corpus may be stale — price history insufficient for full check.",
        "synthesis": "Research synthesis",
        "agent_answer": "Serenity research answer",
        "agent_answer_sub": "Synthesizes corpus thesis + live data to answer your question",
        "supporting_data": "Supporting data",
        "references": "References",
        "show_more": "Show more",
        "show_less": "Show less",
        "key_evidence": "Key evidence",
        "attention": "Serenity attention on this ticker",
        "signal_type": "Signal type",
        "mentions_14d": "Mentions (last 14d)",
        "momentum": "Momentum vs prior 14d",
        "signal_heating": "Heating — mention velocity rising",
        "signal_new": "New entrant — first seen in window",
        "signal_conviction": "Conviction watch — repeated + active",
        "daily_brief": "Daily brief",
        "brief_missing": "No daily brief file — run scripts/daily_brief.ps1 first.",
        "mode_a_title": "Ticker view",
        "mode_b_title": "Attention radar",
        "mode_c_title": "Theme & supply-chain scan",
        "mode_d_title": "Research memo",
        "mode_e_title": "Method coaching",
        "mode_brief_title": "Daily brief summary",
        "prev_14d": "Prior 14d",
        "llm_pending": "Add DEEPSEEK_API_KEY in .env for extended agent narrative.",
        "theme_live_web": "Theme live web scan",
        "theme_live_note": "Industry scan uses news search — not a single-stock chart. Layer ranking and stock shortlist come from the agent narrative.",
    },
    "zh": {
        "ticker_lookup": "标的分析",
        "corpus_thesis": "Serenity 语料观点",
        "live_market": "实时市场数据",
        "recent_tweets": "近期推文",
        "web_sources": "联网来源",
        "radar": "注意力雷达",
        "corpus_vs_live": "语料 vs 实时市场",
        "fresh_name": "新标的 — 语料未覆盖",
        "partial": "部分覆盖",
        "disclaimer": "独立研究蒸馏工具 — 非 Serenity 本人，不构成投资建议。",
        "deep_thesis": "已有深度 thesis",
        "no_thesis": "语料中无深度 thesis",
        "price": "现价",
        "change_1d": "日涨跌",
        "range_52w": "52周区间",
        "market_cap": "市值",
        "exchange": "交易所",
        "instrument": "标的",
        "crypto_spot_note": "加密货币现货价（Yahoo），非股票 ETF。",
        "as_of": "更新时间",
        "signal": "Radar 信号",
        "stale_hint": "对比 thesis 日期与现价/新闻；若实质变化较大，标为 stale。",
        "metric": "指标",
        "value": "数值",
        "source": "来源",
        "title": "标题",
        "date": "日期",
        "type": "类型",
        "velocity": "动量",
        "recent": "近期提及",
        "ticker": "代码",
        "theme": "主题",
        "delta": "变化",
        "stale_title": "Thesis 新鲜度",
        "stale_fresh": "语料日期较新 — 仍需对照实时数据。",
        "stale_watch": "语料偏旧 — 请关注价格与新闻。",
        "stale_yes": "⚠️ Thesis 可能 stale — 语料日期与现价变化建议重新核验。",
        "stale_soft": "⚠️ 语料可能过时 — 价格历史不足以完整判断。",
        "synthesis": "研究综合",
        "agent_answer": "Serenity 研究回答",
        "agent_answer_sub": "综合语料观点与实时数据，直接回答你的问题",
        "supporting_data": "支撑数据",
        "references": "参考来源",
        "show_more": "展开",
        "show_less": "收起",
        "key_evidence": "关键证据",
        "attention": "Serenity 对该标的注意力",
        "signal_type": "信号类型",
        "mentions_14d": "近 14 天提及次数",
        "momentum": "相对前 14 天动量",
        "signal_heating": "升温 — 提及加速",
        "signal_new": "新进 — 窗口内首次出现",
        "signal_conviction": "信念观察 — 反复提及且仍活跃",
        "daily_brief": "Daily brief",
        "brief_missing": "未找到 daily brief — 请先运行 scripts/daily_brief.ps1",
        "mode_a_title": "单标的观点",
        "mode_b_title": "注意力 Radar",
        "mode_c_title": "主题产业链扫描",
        "mode_d_title": "研报输出",
        "mode_e_title": "方法论辅导",
        "mode_brief_title": "Daily brief 摘要",
        "prev_14d": "前 14 天",
        "llm_pending": "在 .env 配置 DEEPSEEK_API_KEY 可启用扩展 Agent 叙述。",
        "theme_live_web": "主题联网检索",
        "theme_live_note": "产业链扫描以新闻检索为主，不展示单股走势图。层级排序与个股 shortlist 由 Agent 叙述输出。",
    },
}


def _t(locale: str, key: str) -> str:
    return LABELS.get(locale, LABELS["en"]).get(key, key)


def _esc(s: Any) -> str:
    return html.escape(str(s) if s is not None else "")


def _fmt_num(n: Any, *, suffix: str = "") -> str:
    if n is None:
        return "—"
    try:
        f = float(n)
        if abs(f) >= 1e9:
            return f"{f/1e9:.2f}B{suffix}"
        if abs(f) >= 1e6:
            return f"{f/1e6:.2f}M{suffix}"
        if abs(f) >= 100:
            return f"{f:,.2f}{suffix}"
        return f"{f:.2f}{suffix}"
    except (TypeError, ValueError):
        return str(n)


def _fmt_pct(p: Any) -> str:
    if p is None:
        return "—"
    try:
        v = float(p)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.2f}%"
    except (TypeError, ValueError):
        return "—"


def _summarize_thesis(md: str, *, max_lines: int = 12) -> tuple[str, str, bool]:
    if not md:
        return "", "", False
    lines = [ln.rstrip() for ln in md.splitlines()]
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else ""
    if not title:
        for ln in lines:
            if ln.startswith("###"):
                title = ln.lstrip("# ").strip()
                break
    return title, "", False


_THESIS_TIER = {
    "thesis": "primary",
    "latest stance": "primary",
    "tier evolution": "secondary",
    "article support": "tertiary",
    "key evidence": "detail",
}

_EVIDENCE_SPLIT = re.compile(
    r"(?<=[.;])\s+(?=(?:Later |A later |"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d+))"
)


def _thesis_tier(label: str) -> str:
    return _THESIS_TIER.get(label.lower().strip(), "secondary")


def _split_thesis_body(body: str, label: str) -> list[str]:
    if not body:
        return []
    key = label.lower().strip()
    if key != "key evidence" and len(body) < 320:
        return [body]
    parts = [p.strip() for p in _EVIDENCE_SPLIT.split(body) if p.strip()]
    if len(parts) <= 1 and key == "key evidence":
        parts = [p.strip() for p in re.split(r";\s+", body) if p.strip()]
    if len(parts) <= 1:
        return [body]
    return parts


def _parse_thesis_bullets(md: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not md:
        return items
    current: dict[str, Any] | None = None
    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith("###"):
            if current:
                items.append(current)
            current = None
            continue
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line)
        if m:
            if current:
                items.append(current)
            label = m.group(1).strip()
            body = m.group(2).strip()
            subitems = _split_thesis_body(body, label)
            current = {
                "label": label,
                "body": body,
                "subitems": subitems if len(subitems) > 1 else [],
                "tier": _thesis_tier(label),
                "collapsed": _thesis_tier(label) == "detail",
            }
            continue
        if current and line and not line.startswith("- "):
            current["body"] = (current["body"] + " " + line).strip()
            subitems = _split_thesis_body(current["body"], current["label"])
            current["subitems"] = subitems if len(subitems) > 1 else []
    if current:
        items.append(current)
    order = {"primary": 0, "secondary": 1, "tertiary": 2, "detail": 3}
    items.sort(key=lambda x: order.get(x.get("tier", "secondary"), 2))
    return items


def _signal_label(locale: str, signal: str) -> str:
    key = {
        "heating": "signal_heating",
        "new_entrants": "signal_new",
        "conviction_watch": "signal_conviction",
    }.get(signal, "")
    return _t(locale, key) if key else signal.replace("_", " ").title()


def _parse_brief_heating(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    in_heating = False
    for line in text.splitlines():
        if "Heating" in line or "升温" in line:
            in_heating = True
            continue
        if in_heating and line.startswith("##"):
            break
        if in_heating and line.strip().startswith("ticker="):
            parts = dict(p.split("=", 1) for p in line.split() if "=" in p)
            delta = parts.get("delta", "0")
            try:
                d = int(delta)
                delta_fmt = f"+{d}" if d > 0 else str(d)
            except ValueError:
                delta_fmt = delta
            rows.append([parts.get("ticker", "—"), parts.get("recent", "—"), delta_fmt, parts.get("prev", "—")])
    return rows


def _mode_title(mode: str, locale: str) -> str:
    return _t(locale, f"mode_{mode.lower()}_title") if mode in ("A", "B", "C", "D", "E") else _t(locale, "mode_brief_title")


def _build_synthesis_bullets(ctx: dict[str, Any], mode: str, locale: str) -> list[str]:
    bullets: list[str] = []
    lookup = ctx.get("lookup") or {}
    ticker = ctx.get("ticker")
    th = lookup.get("thesis") or {}
    parsed = _parse_thesis_bullets(th.get("markdown") or "")

    if mode == "A" and ticker:
        for item in parsed:
            if item["label"].lower() in ("stance", "tier", "latest stance"):
                bullets.append(f"{item['label']}: {item['body'][:220]}")
        radar = lookup.get("radar")
        if radar:
            bullets.append(
                f"{_t(locale, 'attention')}: {_signal_label(locale, radar.get('signal', ''))} — "
                f"{_t(locale, 'mentions_14d')} {radar.get('recent', '—')}, "
                f"{_t(locale, 'momentum')} {radar.get('delta', radar.get('velocity', '—'))}"
            )
        stale = ctx.get("stale") or {}
        if stale.get("level") in ("stale", "stale_soft", "watch"):
            bullets.append(_t(locale, stale.get("level") == "watch" and "stale_watch" or "stale_yes"))
        if not bullets and parsed:
            bullets.append(parsed[0]["body"][:240])

    elif mode == "B" and ctx.get("radar"):
        r = ctx["radar"]
        for row in (r.get("heating") or [])[:5]:
            bullets.append(f"${row.get('ticker')} — {_t(locale, 'mentions_14d')} {row.get('recent')}, {_t(locale, 'momentum')} +{row.get('velocity', row.get('delta', 0))}")
        for row in (r.get("new_entrants") or [])[:3]:
            bullets.append(f"${row.get('ticker')} — {_t(locale, 'signal_new')} ({row.get('recent')} mentions)")
        if not bullets:
            bullets.append("No heating tickers in the current 14d window.")

    elif mode == "brief":
        brief = ctx.get("daily_brief")
        if not brief:
            bullets.append(_t(locale, "brief_missing"))
        else:
            rows = _parse_brief_heating(brief)
            for row in rows[:6]:
                bullets.append(f"${row[0]} — {_t(locale, 'mentions_14d')} {row[1]}, {_t(locale, 'momentum')} {row[2]} (was {row[3]})")
            if ctx.get("radar"):
                bullets.append("Cross-check heating names against corpus theses in tables below.")

    elif mode == "C":
        live = ctx.get("live_web") or {}
        query = (live.get("query") or "")[:120]
        if locale == "en":
            if query:
                bullets.append(f"Theme query: {query}")
            bullets.extend([
                "Layer ranking: scarce supply → design-around risk → beneficiaries.",
                "Name stocks only after layers are ranked.",
                "ETF fit only when explicitly requested.",
            ])
        else:
            if query:
                bullets.append(f"主题检索：{query}")
            bullets.extend([
                "层级排序：稀缺供给 → 难替代 → 受益环节。",
                "先排层，再落到个股。",
                "仅用户明确询问时讨论 ETF。",
            ])

    elif mode == "D":
        bullets.extend([
            f"One-page memo for ${ticker or 'target'}: system change → bottleneck → evidence ladder → falsifiers.",
            "Use corpus thesis as anchor; live web for verification.",
            "Flag stale thesis if corpus date vs price diverges.",
        ] if locale == "en" else [
            f"输出 ${ticker or '标的'} 单页 memo：系统变化 → 卡点 → 证据阶梯 → 证伪条件。",
            "以语料 thesis 为锚，联网数据作核验。",
            "语料日期与价格偏离时标注 stale。",
        ])

    elif mode == "E":
        bullets.extend([
            "Coaching mode — one question at a time, no stock picks.",
            "Tickers in examples are illustrative only.",
            "Start from hyperscaler capex → upstream bottleneck framework.",
        ] if locale == "en" else [
            "辅导模式 — 每次只问一个问题，不提供荐股。",
            "举例 ticker 仅作说明。",
            "从 hyperscaler capex → 上游瓶颈框架开始。",
        ])

    return bullets[:8]


def render_synthesis_html(ctx: dict[str, Any], mode: str, locale: str, *, llm_pending: bool = False) -> str:
    bullets = _build_synthesis_bullets(ctx, mode, locale)
    if not bullets:
        return ""
    items = "".join(f"<li>{_esc(b)}</li>" for b in bullets)
    note = f'<p class="synthesis-note">{_esc(_t(locale, "llm_pending"))}</p>' if llm_pending else ""
    return (
        f'<section class="report-section synthesis-section"><h2>{_esc(_t(locale, "synthesis"))}</h2>'
        f'<ul class="synthesis-list">{items}</ul>{note}</section>'
    )


def render_agent_slot(locale: str, *, hidden: bool = True) -> str:
    cls = "report-section agent-hero llm-narrative-section" + (" hidden" if hidden else "")
    return (
        f'<section class="{cls}">'
        f'<h2>{_esc(_t(locale, "agent_answer"))}</h2>'
        f'<p class="agent-hero-sub">{_esc(_t(locale, "agent_answer_sub"))}</p>'
        f'<div class="llm-narrative agent-narrative"></div></section>'
    )


def render_llm_markdown(text: str) -> str:
    from serenity_twin.agent_markdown import render_agent_markdown

    return render_agent_markdown(text)


def build_structured(
    ctx: dict[str, Any],
    mode: str,
    locale: str = "zh",
    *,
    suppress_synthesis: bool = False,
) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    support: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    ticker = ctx.get("ticker")
    lookup = ctx.get("lookup") or {}
    live = ctx.get("live_web") or {}

    subtitle = f"Mode {mode}"
    if ticker:
        subtitle += f" · ${ticker}"
    elif mode in ("C", "D") and live.get("query"):
        subtitle += f" · {(live.get('query') or '')[:72]}"
    sections.append(
        {
            "type": "header",
            "title": _mode_title(mode, locale),
            "subtitle": subtitle,
            "badges": [{"text": "Live web" if live else "Corpus", "tone": "live" if live else "ok"}],
        }
    )

    synth_bullets = _build_synthesis_bullets(ctx, mode, locale)
    if synth_bullets and not suppress_synthesis:
        sections.append({"type": "insight", "title": _t(locale, "synthesis"), "bullets": synth_bullets})

    if mode == "brief":
        brief = ctx.get("daily_brief")
        if brief:
            rows = _parse_brief_heating(brief)
            if rows:
                support.append(
                    {
                        "type": "table",
                        "title": f"{_t(locale, 'daily_brief')} — {'Heating' if locale == 'en' else '升温'}",
                        "headers": [_t(locale, "ticker"), _t(locale, "mentions_14d"), _t(locale, "momentum"), _t(locale, "prev_14d")],
                        "rows": rows[:12],
                    }
                )
        else:
            support.append({"type": "alert", "level": "warning", "title": _t(locale, "daily_brief"), "text": _t(locale, "brief_missing")})

    if mode == "B" and ctx.get("radar"):
        r = ctx["radar"]
        for block_key, block_title in (
            ("heating", "Heating" if locale == "en" else "升温"),
            ("new_entrants", "New entrants" if locale == "en" else "新进"),
            ("conviction_watch", "Conviction" if locale == "en" else "信念观察"),
        ):
            rows = r.get(block_key) or []
            if rows:
                support.append(
                    {
                        "type": "table",
                        "title": f"{_t(locale, 'radar')} — {block_title}",
                        "headers": [_t(locale, "ticker"), _t(locale, "recent"), _t(locale, "velocity") if block_key == "heating" else "Total"],
                        "rows": [[row.get("ticker"), row.get("recent"), row.get("velocity") if block_key == "heating" else row.get("total")] for row in rows[:10]],
                    }
                )
        themes = r.get("theme_rotation") or []
        if themes:
            support.append(
                {
                    "type": "table",
                    "title": "Theme rotation" if locale == "en" else "主题轮动",
                    "headers": [_t(locale, "theme"), _t(locale, "recent"), _t(locale, "delta")],
                    "rows": [[t.get("theme"), t.get("recent"), t.get("delta")] for t in themes[:8]],
                }
            )

    if mode == "brief" and ctx.get("radar"):
        r = ctx["radar"]
        heating = r.get("heating") or []
        if heating:
            support.append(
                {
                    "type": "table",
                    "title": f"{_t(locale, 'radar')} — {'Live snapshot' if locale == 'en' else '实时快照'}",
                    "headers": [_t(locale, "ticker"), _t(locale, "recent"), _t(locale, "velocity")],
                    "rows": [[row.get("ticker"), row.get("recent"), row.get("velocity")] for row in heating[:8]],
                }
            )

    if mode in ("C", "D") and not ticker and live.get("query"):
        support.append(
            {
                "type": "alert",
                "level": "info",
                "title": _t(locale, "theme_live_web"),
                "text": _t(locale, "theme_live_note"),
            }
        )
        theme_searches = live.get("news_search") or []
        if theme_searches and theme_searches[0].get("title") != "search_error":
            support.append(
                {
                    "type": "sources",
                    "title": _t(locale, "web_sources"),
                    "items": [
                        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": (r.get("snippet") or "")[:180]}
                        for r in theme_searches[:8]
                    ],
                }
            )

    if ticker and mode in ("A", "D", "E"):
        support.append(
            {
                "type": "header",
                "title": f"${ticker}",
                "subtitle": _t(locale, "ticker_lookup"),
                "badges": [
                    {"text": _t(locale, "deep_thesis") if lookup.get("found_in_theses") else _t(locale, "no_thesis"), "tone": "ok" if lookup.get("found_in_theses") else "muted"},
                ],
            }
        )

    quote = live.get("quote") if isinstance(live.get("quote"), dict) else live if live.get("regular_market_price") else None
    if quote and quote.get("status") == "ok":
        inst = quote.get("short_name") or quote.get("yahoo_symbol") or f"${ticker}"
        ysym = quote.get("yahoo_symbol") or ""
        if ysym and ysym not in inst:
            inst = f"{inst} ({ysym})"
        rows = [
            [_t(locale, "instrument"), inst],
            [_t(locale, "price"), f"{_fmt_num(quote.get('regular_market_price'))} {quote.get('currency') or ''}".strip()],
            [_t(locale, "change_1d"), _fmt_pct(quote.get("change_pct_1d"))],
            [_t(locale, "range_52w"), f"{_fmt_num(quote.get('fifty_two_week_low'))} – {_fmt_num(quote.get('fifty_two_week_high'))}"],
            [_t(locale, "exchange"), quote.get("exchange") or ysym or "—"],
        ]
        if quote.get("market_cap"):
            rows.append([_t(locale, "market_cap"), _fmt_num(quote.get("market_cap"))])
        support.append(
            {
                "type": "table",
                "title": _t(locale, "live_market"),
                "headers": [_t(locale, "metric"), _t(locale, "value")],
                "rows": rows,
                "footnote": (
                    f"{_t(locale, 'as_of')}: {(quote.get('as_of') or live.get('fetched_at') or '')[:19]}"
                    + (f" · {_t(locale, 'crypto_spot_note')}" if quote.get("instrument_type") == "crypto_spot" else "")
                ),
                "compact": True,
            }
        )
        hist = quote.get("price_history")
        if hist and hist.get("values"):
            support.append(
                {
                    "type": "chart",
                    "title": "3M" if locale == "en" else "近3月走势",
                    "chartType": "line",
                    "labels": hist.get("labels", []),
                    "values": hist.get("values", []),
                    "currency": quote.get("currency"),
                    "compact": True,
                }
            )

    if lookup.get("found_in_theses"):
        th = lookup.get("thesis") or {}
        title, _, _ = _summarize_thesis(th.get("markdown") or "")
        bullets = _parse_thesis_bullets(th.get("markdown") or "")
        support.append(
            {
                "type": "thesis",
                "title": _t(locale, "corpus_thesis"),
                "sector": th.get("sector"),
                "file": th.get("file"),
                "heading": title or th.get("title") or f"${ticker}",
                "bullets": bullets,
            }
        )
    elif lookup and ticker and not lookup.get("found_in_theses"):
        tweets = lookup.get("recent_tweets") or []
        if not tweets:
            support.append({"type": "alert", "level": "info", "title": _t(locale, "fresh_name"), "text": _t(locale, "stale_hint")})
        else:
            support.append({"type": "alert", "level": "info", "title": _t(locale, "partial"), "text": _t(locale, "stale_hint")})

    radar = lookup.get("radar")
    if radar:
        delta = radar.get("delta", radar.get("velocity", "—"))
        try:
            d = int(delta)
            delta_fmt = f"+{d}" if d > 0 else str(d)
        except (TypeError, ValueError):
            delta_fmt = str(delta)
        support.append(
            {
                "type": "table",
                "title": _t(locale, "attention"),
                "headers": [_t(locale, "metric"), _t(locale, "value")],
                "rows": [
                    [_t(locale, "signal_type"), _signal_label(locale, radar.get("signal", ""))],
                    [_t(locale, "mentions_14d"), str(radar.get("recent", "—"))],
                    [_t(locale, "momentum"), delta_fmt],
                    [_t(locale, "prev_14d"), str(radar.get("prev", "—"))],
                ],
                "footnote": "Heating = mention count rising vs prior 14d window." if locale == "en" else "升温 = 近 14 天提及次数相对前 14 天上升。",
                "compact": True,
            }
        )

    tweets = lookup.get("recent_tweets") or []
    if tweets:
        references.append(
            {
                "type": "tweets",
                "title": _t(locale, "recent_tweets"),
                "items": [
                    {"date": (t.get("created_at") or "")[:10], "kind": t.get("kind", "post"), "url": t.get("url", "#"), "text": t.get("text_preview", "")}
                    for t in tweets[:3]
                ],
            }
        )

    searches = live.get("news_search") or []
    theme_news_in_support = mode in ("C", "D") and not ticker and live.get("query")
    if searches and searches[0].get("title") != "search_error" and not theme_news_in_support:
        references.append(
            {
                "type": "sources",
                "title": _t(locale, "web_sources"),
                "items": [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": (r.get("snippet") or "")[:140]} for r in searches[:5]],
            }
        )

    if live.get("sec_filings"):
        references.append(
            {
                "type": "table",
                "title": "SEC filings" if locale == "en" else "SEC 披露",
                "headers": ["Form", "Filed", "Entity"],
                "rows": [[f.get("form"), f.get("filed"), f.get("entity")] for f in live["sec_filings"][:5]],
            }
        )

    stale = ctx.get("stale")
    if stale and lookup.get("found_in_theses"):
        level_map = {"stale": "warning", "stale_soft": "warning", "watch": "info", "fresh": "info", "ok": "info"}
        msg_key = {"stale": "stale_yes", "stale_soft": "stale_soft", "watch": "stale_watch", "fresh": "stale_fresh", "ok": "stale_fresh"}
        detail: list[str] = []
        if stale.get("latest_corpus_date"):
            age = stale.get("age_days")
            detail.append(f"{stale['latest_corpus_date']}" + (f" ({age}d)" if age is not None else ""))
        if stale.get("price_change_pct_since_corpus") is not None:
            detail.append(f"{stale['price_change_pct_since_corpus']:+.1f}% since corpus")
        text = _t(locale, msg_key.get(stale.get("level", "ok"), "stale_hint"))
        if detail:
            text = f"{text} ({', '.join(detail)})"
        support.append({"type": "alert", "level": level_map.get(stale.get("level"), "info"), "title": _t(locale, "stale_title"), "text": text})

    if support:
        sections.append({"type": "group", "title": _t(locale, "supporting_data"), "sections": support})
    if references:
        sections.append(
            {
                "type": "collapsible",
                "title": _t(locale, "references"),
                "default_open": False,
                "sections": references,
            }
        )

    sections.append({"type": "disclaimer", "text": _t(locale, "disclaimer")})
    return {"mode": mode, "ticker": ticker, "locale": locale, "sections": sections, "stale": stale}


def _render_section(sec: dict[str, Any], locale: str = "en") -> str:
    st = sec.get("type")
    if st == "header":
        badges = "".join(f'<span class="badge badge-{b.get("tone","muted")}">{_esc(b["text"])}</span>' for b in sec.get("badges", []))
        return (
            f'<header class="report-header"><h1>{_esc(sec.get("title"))}</h1>'
            f'<p class="report-sub">{_esc(sec.get("subtitle"))}</p><div class="badges">{badges}</div></header>'
        )
    if st == "metrics":
        items = "".join(
            f'<div class="metric-card"><div class="metric-label">{_esc(it.get("label"))}</div>'
            f'<div class="metric-value">{_esc(it.get("value"))}</div>'
            f'<div class="metric-delta">{_esc(it.get("delta",""))}</div></div>'
            for it in sec.get("items", [])
        )
        title = f'<h2>{_esc(sec["title"])}</h2>' if sec.get("title") else ""
        return f'<section class="report-section metrics-grid">{title}{items}</section>'
    if st == "table":
        head = "".join(f"<th>{_esc(h)}</th>" for h in sec.get("headers", []))
        rows = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in sec.get("rows", [])
        )
        foot = f'<p class="footnote">{_esc(sec["footnote"])}</p>' if sec.get("footnote") else ""
        compact = " report-section-compact" if sec.get("compact") else ""
        return (
            f'<section class="report-section{compact}"><h2>{_esc(sec.get("title",""))}</h2>'
            f'<div class="table-wrap"><table class="data-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>{foot}</section>'
        )
    if st == "chart":
        import json as _json

        cid = f"chart-{abs(hash(sec.get('title'))) % 100000}"
        labels_attr = _json.dumps(sec.get("labels", []))
        values_attr = _json.dumps(sec.get("values", []))
        compact = " chart-section-compact" if sec.get("compact") else ""
        return (
            f'<section class="report-section chart-section{compact}"><h2>{_esc(sec.get("title",""))}</h2>'
            f'<canvas id="{cid}" class="price-chart" data-labels=\'{labels_attr}\' '
            f"data-values='{values_attr}' data-currency=\"{_esc(sec.get('currency',''))}\"></canvas></section>"
        )
    if st == "thesis":
        meta = f'<span class="thesis-meta">{_esc(sec.get("sector",""))}</span>'
        bullets = sec.get("bullets") or []
        card_parts: list[str] = []
        for b in bullets:
            tier = b.get("tier", "secondary")
            subitems = b.get("subitems") or []
            collapsed = b.get("collapsed") and subitems
            preview = subitems[0] if subitems else b.get("body", "")
            if collapsed:
                timeline = "".join(f"<li>{_esc(item)}</li>" for item in subitems)
                body_html = (
                    f'<p class="thesis-card-preview">{_esc(preview[:220])}{"…" if len(preview) > 220 else ""}</p>'
                    f'<ul class="thesis-timeline hidden">{timeline}</ul>'
                    f'<button type="button" class="text-btn toggle-evidence" data-show="{_esc(_t(locale, "show_more"))}" '
                    f'data-hide="{_esc(_t(locale, "show_less"))}">{_esc(_t(locale, "show_more"))}</button>'
                )
            elif subitems:
                timeline = "".join(f"<li>{_esc(item)}</li>" for item in subitems)
                body_html = f'<ul class="thesis-timeline">{timeline}</ul>'
            else:
                body_html = f'<p class="thesis-card-body">{_esc(b.get("body"))}</p>'
            card_parts.append(
                f'<div class="thesis-card thesis-tier-{tier}"><div class="thesis-card-label">{_esc(b.get("label"))}</div>{body_html}</div>'
            )
        cards = "".join(card_parts)
        return (
            f'<section class="report-section thesis-block"><h2>{_esc(sec.get("title"))}</h2>{meta}'
            f'<h3 class="thesis-heading">{_esc(sec.get("heading",""))}</h3>'
            f'<div class="thesis-cards">{cards}</div></section>'
        )
    if st == "insight":
        items = "".join(f"<li>{_esc(b)}</li>" for b in sec.get("bullets", []))
        return (
            f'<section class="report-section insight-section"><h2>{_esc(sec.get("title"))}</h2>'
            f'<ul class="synthesis-list">{items}</ul></section>'
        )
    if st == "tweets":
        items = "".join(
            f'<article class="tweet-card tweet-card-compact"><div class="tweet-meta"><time>{_esc(t.get("date"))}</time>'
            f'<span class="tweet-kind">{_esc(t.get("kind"))}</span></div>'
            f'<p>{_esc(t.get("text"))}</p>'
            f'<a href="{_esc(t.get("url"))}" target="_blank" rel="noopener">Source ↗</a></article>'
            for t in sec.get("items", [])
        )
        return f'<section class="report-section report-section-ref"><h2>{_esc(sec.get("title"))}</h2><div class="tweet-list">{items}</div></section>'
    if st == "sources":
        items = "".join(
            f'<a class="source-card source-card-compact" href="{_esc(s.get("url"))}" target="_blank" rel="noopener">'
            f'<div class="source-title">{_esc(s.get("title"))}</div>'
            f'<div class="source-snippet">{_esc(s.get("snippet"))}</div></a>'
            for s in sec.get("items", [])
        )
        return f'<section class="report-section report-section-ref"><h2>{_esc(sec.get("title"))}</h2><div class="source-grid">{items}</div></section>'
    if st == "alert":
        return (
            f'<div class="alert alert-{sec.get("level","info")}"><strong>{_esc(sec.get("title",""))}</strong>'
            f'<p>{_esc(sec.get("text",""))}</p></div>'
        )
    if st == "disclaimer":
        return f'<p class="disclaimer">{_esc(sec.get("text"))}</p>'
    if st == "group":
        inner = "".join(_render_section(child, locale) for child in sec.get("sections", []))
        return f'<div class="report-group"><h2 class="report-group-title">{_esc(sec.get("title",""))}</h2>{inner}</div>'
    if st == "collapsible":
        inner = "".join(_render_section(child, locale) for child in sec.get("sections", []))
        open_attr = " open" if sec.get("default_open") else ""
        return (
            f'<details class="report-collapsible"{open_attr}>'
            f'<summary>{_esc(sec.get("title",""))}</summary><div class="report-collapsible-body">{inner}</div></details>'
        )
    return ""


def render_html(structured: dict[str, Any]) -> str:
    locale = structured.get("locale", "en")
    parts: list[str] = ['<div class="report">']
    for sec in structured.get("sections", []):
        html = _render_section(sec, locale)
        if html:
            parts.append(html)
    parts.append("</div>")
    return "".join(parts)
