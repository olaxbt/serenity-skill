"""Automatic live web research — quotes, news search, SEC filings (stdlib only)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from serenity_twin.paths import ROOT

ENV_FILE = ROOT / ".env"
USER_AGENT = "SerenityTwin/0.3 (research-ui; +https://github.com/olaxbt/serenity-skill)"
REQUEST_TIMEOUT = 10
PROBE_TIMEOUT = 5
MAX_YAHOO_SUFFIX_TRIES = 2


def _http_get(url: str, *, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _http_post(url: str, data: bytes, *, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


# Plain tickers that collide with equity/ETF listings on Yahoo — map to crypto spot.
CRYPTO_SPOT_ALIASES: dict[str, str] = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "DOGE": "DOGE-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "BNB": "BNB-USD",
    "AVAX": "AVAX-USD",
    "DOT": "DOT-USD",
    "LINK": "LINK-USD",
}


def yahoo_symbol(ticker: str) -> str:
    t = ticker.upper().strip().lstrip("$")
    if t in CRYPTO_SPOT_ALIASES:
        return CRYPTO_SPOT_ALIASES[t]
    if re.fullmatch(r"\d{6}", t):
        # A-share heuristic: 6xxxxx → Shanghai, else Shenzhen
        return f"{t}.SS" if t.startswith("6") else f"{t}.SZ"
    if re.fullmatch(r"\d{5}", t):
        return f"{t}.HK"
    return t


def is_crypto_spot_symbol(yahoo_sym: str) -> bool:
    return yahoo_sym.upper().endswith("-USD") and yahoo_sym.split("-")[0] in CRYPTO_SPOT_ALIASES


def fetch_quote(ticker: str) -> dict[str, Any]:
    """Latest price snapshot via Yahoo Finance chart API (unofficial, no key)."""
    t = ticker.upper().lstrip("$")
    candidates = [yahoo_symbol(t)]
    # Crypto spot — do not fall through to equity/ETF tickers with the same symbol (e.g. BTC ETF ~$27).
    if t in CRYPTO_SPOT_ALIASES:
        candidates = [CRYPTO_SPOT_ALIASES[t]]
    elif re.fullmatch(r"[A-Z]{2,5}", t):
        for suffix in (".ST", ".OL"):
            alt = f"{t}{suffix}"
            if alt not in candidates:
                candidates.append(alt)

    last_error = ""
    suffix_tries = 0
    for sym in candidates:
        if sym != t:
            suffix_tries += 1
            if suffix_tries > MAX_YAHOO_SUFFIX_TRIES:
                break
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + urllib.parse.quote(sym)
            + "?interval=1d&range=3mo"
        )
        out: dict[str, Any] = {"ticker": t, "yahoo_symbol": sym, "status": "ok"}
        try:
            raw = _http_get(url)
            data = json.loads(raw)
            result = data.get("chart", {}).get("result")
            if not result:
                last_error = "empty chart result"
                continue
            meta = result[0]["meta"]
            if meta.get("regularMarketPrice") is None:
                last_error = "no price in meta"
                continue
            chart = result[0]
            closes = (chart.get("indicators") or {}).get("quote", [{}])[0].get("close") or []
            timestamps = chart.get("timestamp") or []
            valid_pairs = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
            change_pct = None
            if len(valid_pairs) >= 2:
                prev_c, last_c = valid_pairs[-2][1], valid_pairs[-1][1]
                if prev_c and abs(prev_c) > 1e-9:
                    change_pct = round((last_c - prev_c) / prev_c * 100, 2)
            elif meta.get("regularMarketPrice") and meta.get("previousClose"):
                pc = float(meta["previousClose"])
                if pc > 1e-9:
                    raw_pct = (float(meta["regularMarketPrice"]) - pc) / pc * 100
                    if abs(raw_pct) <= 50:
                        change_pct = round(raw_pct, 2)

            hist_labels = []
            hist_values = []
            for t, c in valid_pairs[-66:]:
                hist_labels.append(datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"))
                hist_values.append(round(float(c), 4))

            short_name = meta.get("shortName") or meta.get("longName") or sym
            out.update(
                {
                    "currency": meta.get("currency"),
                    "exchange": meta.get("exchangeName"),
                    "short_name": short_name,
                    "instrument_type": "crypto_spot" if is_crypto_spot_symbol(sym) else "equity",
                    "regular_market_price": meta.get("regularMarketPrice"),
                    "previous_close": meta.get("previousClose") or meta.get("chartPreviousClose"),
                    "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
                    "market_cap": meta.get("marketCap"),
                    "change_pct_1d": change_pct,
                    "price_history": {"labels": hist_labels, "values": hist_values},
                    "as_of": datetime.fromtimestamp(
                        meta.get("regularMarketTime") or datetime.now(tz=timezone.utc).timestamp(),
                        tz=timezone.utc,
                    ).isoformat(),
                }
            )
            return out
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            last_error = str(exc)
            continue

    return {"ticker": t, "yahoo_symbol": candidates[0], "status": "error", "error": last_error or "no quote found"}


def search_duckduckgo(query: str, *, max_results: int = 6) -> list[dict[str, str]]:
    """HTML DuckDuckGo search — no API key."""
    results: list[dict[str, str]] = []
    try:
        body = urllib.parse.urlencode({"q": query, "kl": "us-en"}).encode("utf-8")
        html = _http_post(
            "https://html.duckduckgo.com/html/",
            body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # Result blocks: class="result__a" href="..."
        links = re.findall(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for i, (href, title) in enumerate(links[:max_results]):
            title_clean = re.sub(r"<[^>]+>", "", title).strip()
            snippet = ""
            if i < len(snippets):
                snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()[:300]
            # DDG redirect unwrap
            if "uddg=" in href:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = parsed.get("uddg", [href])[0]
            results.append({"title": title_clean, "url": href, "snippet": snippet, "source": "duckduckgo"})
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        results.append({"title": "search_error", "url": "", "snippet": str(exc), "source": "error"})
    return results


def fetch_sec_filings(ticker: str, *, limit: int = 5) -> list[dict[str, str]]:
    """Recent SEC submissions via EDGAR full-text search (US tickers)."""
    t = ticker.upper().lstrip("$")
    if not re.fullmatch(r"[A-Z]{1,5}", t):
        return []
    q = urllib.parse.quote(f'"{t}"')
    url = (
        "https://efts.sec.gov/LATEST/search-index?"
        f"q={q}&forms=10-K,10-Q,8-K,S-1&dateRange=custom&startdt=2024-01-01"
    )
    filings: list[dict[str, str]] = []
    try:
        raw = _http_get(url)
        data = json.loads(raw)
        hits = data.get("hits", {}).get("hits", [])[:limit]
        for hit in hits:
            src = hit.get("_source", {})
            filings.append(
                {
                    "form": src.get("form", ""),
                    "filed": (src.get("file_date") or src.get("period_ending") or "")[:10],
                    "entity": src.get("display_names", [""])[0] if src.get("display_names") else "",
                    "url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id', '')}/"
                    if src.get("entity_id")
                    else "",
                }
            )
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        pass
    return filings


def research_ticker(ticker: str) -> dict[str, Any]:
    """Full auto live bundle for one ticker."""
    t = ticker.upper().lstrip("$")
    news_query = f"{t} stock earnings SEC filing news"
    return {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "ticker": t,
        "quote": fetch_quote(t),
        "news_search": search_duckduckgo(news_query, max_results=6),
        "sec_filings": fetch_sec_filings(t),
    }


def research_theme(prompt: str) -> dict[str, Any]:
    """Live search for theme / industry prompts (Mode C/D)."""
    # Strip skill prefix noise
    q = re.sub(r"(?i)serenity-twin|用 serenity-twin[:：]?", "", prompt).strip()[:200]
    if not q:
        q = "AI semiconductor supply chain bottleneck 2026"
    return {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "query": q,
        "news_search": search_duckduckgo(q, max_results=8),
    }


def research_radar_tickers(tickers: list[str], *, max_tickers: int = 3) -> dict[str, Any]:
    """Lightweight live pass for top radar names."""
    out: dict[str, Any] = {"fetched_at": datetime.now(tz=timezone.utc).isoformat(), "tickers": {}}
    for t in tickers[:max_tickers]:
        out["tickers"][t] = {"quote": fetch_quote(t), "news_search": search_duckduckgo(f"{t} stock news", max_results=3)}
    return out


def format_live_web_markdown(live: dict[str, Any]) -> str:
    lines = ["## Live web research (auto-fetched)", ""]
    if live.get("fetched_at"):
        lines.append(f"*As of {live['fetched_at']} UTC*")
        lines.append("")

    if "quote" in live and isinstance(live["quote"], dict):
        q = live["quote"]
        lines.append("### Market snapshot")
        if q.get("status") == "ok":
            if q.get("short_name"):
                lines.append(f"- **Instrument:** {q.get('short_name')} (`{q.get('yahoo_symbol')}`)")
            lines.append(f"- **Price:** {q.get('regular_market_price')} {q.get('currency', '')}")
            if q.get("change_pct_1d") is not None:
                lines.append(f"- **1d change:** {q.get('change_pct_1d')}%")
            if q.get("market_cap"):
                lines.append(f"- **Market cap:** {q.get('market_cap')}")
            lines.append(f"- **52w range:** {q.get('fifty_two_week_low')} – {q.get('fifty_two_week_high')}")
        else:
            lines.append(f"- Quote unavailable: {q.get('error', 'unknown')}")
        lines.append("")

    if live.get("sec_filings"):
        lines.append("### Recent SEC filings (US)")
        for f in live["sec_filings"][:5]:
            lines.append(f"- {f.get('form')} filed {f.get('filed')} — {f.get('entity')}")
        lines.append("")

    searches = live.get("news_search") or []
    if searches:
        lines.append("### Web sources (news / search)")
        for i, r in enumerate(searches[:8], 1):
            if r.get("title") == "search_error":
                lines.append(f"- Search error: {r.get('snippet')}")
                continue
            lines.append(f"{i}. [{r.get('title', 'link')}]({r.get('url', '#')})")
            if r.get("snippet"):
                lines.append(f"   {r['snippet'][:200]}")
        lines.append("")

    if live.get("tickers"):
        lines.append("### Radar ticker snapshots")
        for t, bundle in live["tickers"].items():
            q = bundle.get("quote", {})
            px = q.get("regular_market_price", "n/a")
            lines.append(f"- **${t}** price={px} {q.get('currency', '')}")
        lines.append("")

    lines.append("*Grade sources per evidence-ladder.md. Social snippets = leads only.*")
    return "\n".join(lines)


def probe_web_available() -> bool:
    """Startup connectivity check — Yahoo chart API reachable from this machine."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=5d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            resp.read(512)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False
