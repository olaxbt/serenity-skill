"""Theme buckets for radar and mention analytics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    tickers: tuple[str, ...]
    keywords: tuple[str, ...]


THEMES: tuple[Theme, ...] = (
    Theme(
        "CPO / photonics / optical",
        ("SIVE", "AAOI", "LITE", "COHR", "POET", "JBL", "AXTI", "SOI", "IQE", "TSEM", "MTSI", "LPK", "AEHR", "CRDO", "GLW", "AEVA", "LPTH", "OSS", "VLN", "ALRIB", "NOK"),
        ("cpo", "photonic", "laser", "optical", "transceiver", "silicon photonics", "inp", "epiwafer", "epitaxial", "substrate", "pluggable", "co-packaged", "fau", "els"),
    ),
    Theme(
        "Power semis / 800VDC / grid",
        ("XFAB", "NVTS", "POWI", "WOLF", "ON", "IFNNY", "ETN", "GEV", "PWR", "HPS.A"),
        ("800vdc", "800 vdc", "sic", "gan", "wide bandgap", "power semi", "power semiconductor", "transformer", "grid"),
    ),
    Theme(
        "AI compute / neocloud / memory",
        ("NVDA", "AMD", "MU", "MRVL", "AVGO", "INTC", "MSFT", "AMZN", "GOOGL", "META", "NBIS", "IREN", "CIFR", "CRWV", "WULF", "ALAB", "TSM", "GFS", "AAPL", "ORCL", "HUT", "BITF", "CLSK", "MARA", "SNDK"),
        ("gpu", "hbm", "asic", "hyperscaler", "data center", "datacenter", "neocloud", "inference", "maia", "tpu", "memory", "mining"),
    ),
    Theme(
        "Western supply chain / policy",
        ("RPI",),
        ("chips act", "funding", "supply chain", "sovereignty", "nist", "msci", "nasdaq", "index inclusion", "europe", "reshoring"),
    ),
    Theme(
        "Space / defense",
        ("RKLB", "ASTS", "SPCE", "SPCX", "LMT", "NOC"),
        ("satcom", "satellite", "space", "defense"),
    ),
    Theme(
        "Fintech / crypto / consumer / squeeze",
        ("HOOD", "SOFI", "BULL", "ETORO", "KSPI", "COIN", "IBIT", "BTC", "MSTR", "CRCL", "HIMS", "UPWK", "GME", "DNUT", "NVO", "UNH", "OSCR", "BKKT", "RDDT", "PYPL", "V", "SG", "OKLO", "IONQ", "QBTS"),
        ("short interest", "squeeze", "etf", "stablecoin", "dilution", "ipo"),
    ),
)


def theme_of(ticker: str, text: str = "") -> str:
    lower = (text or "").lower()
    for th in THEMES:
        if ticker in th.tickers:
            return th.name
    for th in THEMES:
        if any(k in lower for k in th.keywords):
            return th.name
    return "Other"
