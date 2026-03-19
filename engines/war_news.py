"""
engines/war_news.py
===================
Curated intelligence news feed with deterministic per-minute shuffle.
Replace _HEADLINES with a live NewsAPI / GDELT call for production.

Public interface
----------------
    get_war_news(count) -> list[dict]
    get_all_headlines() -> list[dict]
"""

import hashlib
import time
from typing import Any
from engines.gdp_fetcher import get_gdp_data
from engines.gdp_fetcher import fetch_gdp
_SEV_WEIGHT = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# (title, country, severity, category)
_HEADLINES = [
    ("Russia-Ukraine conflict enters critical new offensive phase",              "RU","CRITICAL","CONFLICT"),
    ("NATO member nations pledge additional military aid to Ukraine",             "US","HIGH",    "DIPLOMACY"),
    ("G7 nations finalise expanded sanctions package targeting Russian oil",      "RU","HIGH",    "SANCTIONS"),
    ("IAEA warns of renewed nuclear safety risks at Zaporizhzhia plant",          "RU","CRITICAL","NUCLEAR"),
    ("Russia masses armoured units along northeastern Ukrainian border",          "RU","CRITICAL","CONFLICT"),
    ("China conducts large-scale naval exercises near Taiwan Strait",             "CN","HIGH",    "CONFLICT"),
    ("US Navy freedom-of-navigation patrol challenged in South China Sea",        "US","MEDIUM",  "CONFLICT"),
    ("Taiwan announces record-high defence budget amid PLA escalations",          "CN","HIGH",    "DIPLOMACY"),
    ("Philippines and US hold joint military exercises in disputed waters",       "ID","MEDIUM",  "CONFLICT"),
    ("Saudi Arabia and Houthi forces clash in renewed Yemen offensive",           "SA","HIGH",    "CONFLICT"),
    ("Iran-backed militias conduct drone strikes on US bases in Iraq",            "SA","HIGH",    "CONFLICT"),
    ("Israel conducts airstrikes on Iranian assets in Syria",                     "SA","CRITICAL","CONFLICT"),
    ("Red Sea shipping route disruptions push oil futures to six-month high",     "SA","HIGH",    "ECONOMY"),
    ("North Korea test-fires ICBM; South Korea and US raise alert level",         "KR","CRITICAL","NUCLEAR"),
    ("Seoul and Washington announce expanded joint military readiness exercises",  "KR","HIGH",    "DIPLOMACY"),
    ("India-China LAC border patrol incident escalates into stand-off",           "IN","HIGH",    "CONFLICT"),
    ("Pakistan-India cross-border shelling reported in Kashmir",                  "IN","HIGH",    "CONFLICT"),
    ("India launches carrier strike group into the Indian Ocean",                 "IN","MEDIUM",  "CONFLICT"),
    ("Turkey launches new cross-border operation in northern Syria",              "TR","HIGH",    "CONFLICT"),
    ("Kurdish forces respond to Turkish shelling with rocket barrage",            "TR","MEDIUM",  "CONFLICT"),
    ("Mexico security forces engage cartel in record Sinaloa clash",              "MX","HIGH",    "CONFLICT"),
    ("South Africa deploys peacekeepers to DRC amid intensifying fighting",       "ZA","MEDIUM",  "CONFLICT"),
    ("Argentina and UK trade barbs over Falklands sovereignty at the UN",         "AR","LOW",     "DIPLOMACY"),
    ("IMF cuts G20 growth forecast amid escalating geopolitical risks",           "US","MEDIUM",  "ECONOMY"),
    ("Russia circumvents oil price cap through shadow fleet operations",          "RU","HIGH",    "SANCTIONS"),
    ("Germany accelerates energy independence from Russian gas imports",          "DE","MEDIUM",  "ECONOMY"),
    ("India exploits discounted Russian crude; Western allies warn of risks",     "IN","MEDIUM",  "ECONOMY"),
    ("BRICS nations advance alternative financial settlement framework",          "CN","MEDIUM",  "ECONOMY"),
    ("US Treasury flags Chinese banks for facilitating Russian arms trade",       "CN","HIGH",    "SANCTIONS"),
]

_AGE = ["Just now","1m ago","3m ago","7m ago","12m ago","18m ago","27m ago","38m ago","51m ago","1h ago"]


def _shuffle(count: int, total: int) -> list:
    window = int(time.time() // 60)
    seed   = int(hashlib.sha256(str(window).encode()).hexdigest(), 16)
    idx    = list(range(total))
    s      = seed
    for i in range(total - 1, 0, -1):
        s = (s * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = s % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    return idx[:count]


def get_war_news(count: int = 8) -> list[dict[str, Any]]:
    total   = len(_HEADLINES)
    indices = _shuffle(min(count, total), total)
    picked  = [_HEADLINES[i] for i in indices]
    picked.sort(key=lambda h: _SEV_WEIGHT.get(h[2], 9))
    return [
        {"title": h[0], "country": h[1], "severity": h[2],
         "category": h[3], "age": _AGE[min(i, len(_AGE)-1)]}
        for i, h in enumerate(picked)
    ]


def get_all_headlines() -> list[dict[str, Any]]:
    items = [
        {"title": h[0], "country": h[1], "severity": h[2],
         "category": h[3], "age": _AGE[i % len(_AGE)]}
        for i, h in enumerate(_HEADLINES)
    ]
    items.sort(key=lambda x: _SEV_WEIGHT.get(x["severity"], 9))
    return items
