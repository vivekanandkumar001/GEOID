"""
engines/war_risk.py
===================
Simulates geopolitical war-risk scores for all G20 countries.

Score (0–100) is derived from base risk + military + nuclear
+ alliance + active conflicts + stochastic window noise.

Public interface
----------------
    get_war_risk()     -> dict[str, dict]
    get_risk_summary() -> dict
"""

import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Any
from engines.gdp_fetcher import get_gdp_data
from engines.gdp_fetcher import fetch_gdp
_BASE: dict[str, float] = {
    "US": 18.0, "CN": 42.0, "JP": 12.0, "DE": 10.0, "IN": 36.0,
    "GB": 14.0, "FR": 17.0, "BR": 22.0, "IT": 11.0, "CA":  8.0,
    "KR": 38.0, "AU":  9.0, "MX": 29.0, "ID": 25.0, "TR": 46.0,
    "SA": 53.0, "AR": 21.0, "ZA": 31.0, "RU": 73.0,
}

_MILITARY: dict[str, float] = {
    "US": 86, "CN": 79, "JP": 38, "DE": 42, "IN": 56, "GB": 54,
    "FR": 50, "BR": 28, "IT": 32, "CA": 30, "KR": 62, "AU": 37,
    "MX": 20, "ID": 28, "TR": 58, "SA": 67, "AR": 19, "ZA": 16, "RU": 92,
}

_NUCLEAR: dict[str, float] = {
    "US": 96, "CN": 88, "JP":  0, "DE":  0, "IN": 74, "GB": 82,
    "FR": 84, "BR":  0, "IT":  0, "CA":  0, "KR":  0, "AU":  0,
    "MX":  0, "ID":  0, "TR":  0, "SA":  5, "AR":  0, "ZA":  0, "RU": 99,
}

_ALLIANCE: dict[str, float] = {
    "US": 94, "CN": 52, "JP": 82, "DE": 90, "IN": 44, "GB": 91,
    "FR": 89, "BR": 42, "IT": 86, "CA": 93, "KR": 76, "AU": 89,
    "MX": 52, "ID": 42, "TR": 48, "SA": 48, "AR": 34, "ZA": 38, "RU": 24,
}

_CONFLICTS: dict[str, list] = {
    "RU": ["Ukraine War", "Sanctions Escalation", "Arctic Tensions"],
    "SA": ["Yemen Operations", "Regional Proxy Wars"],
    "TR": ["Syria Operations", "Kurdish Conflict"],
    "IN": ["Kashmir Dispute", "LAC Border Tensions"],
    "CN": ["Taiwan Strait", "South China Sea", "India Border"],
    "KR": ["DPRK Missile Threat"],
    "MX": ["Cartel Warfare"],
    "ZA": ["Regional Instability"],
    "ID": ["Papua Separatism", "Maritime Disputes"],
    "AR": ["Falklands Dispute"],
}

_LEVELS = [(70,"CRITICAL"),(50,"HIGH"),(30,"MEDIUM"),(15,"LOW"),(0,"MINIMAL")]


def _level(score: float) -> str:
    for t, l in _LEVELS:
        if score >= t:
            return l
    return "MINIMAL"


def _noise(code: str) -> float:
    window = int(time.time() // 300)
    h = int(hashlib.md5(f"{code}:{window}".encode()).hexdigest(), 16)
    return (h % 10000 / 10000.0 - 0.5) * 8.0


def _trend(code: str) -> str:
    cur = _BASE[code] + _noise(code)
    prev_win = int(time.time() // 300) - 1
    h2 = int(hashlib.md5(f"{code}:{prev_win}".encode()).hexdigest(), 16)
    prev = _BASE[code] + (h2 % 10000 / 10000.0 - 0.5) * 8.0
    diff = cur - prev
    return "↑" if diff > 1.5 else "↓" if diff < -1.5 else "→"


def _score(code: str) -> float:
    base   = _BASE.get(code, 25.0)
    mil    = (_MILITARY.get(code, 30) - 50) * 0.06
    nuc    = _NUCLEAR.get(code, 0) * 0.04
    ally   = -(_ALLIANCE.get(code, 50) - 50) * 0.05
    conf   = len(_CONFLICTS.get(code, [])) * 1.8
    noise  = _noise(code)
    return round(max(0.0, min(100.0, base + mil + nuc + ally + conf + noise)), 1)


def get_war_risk() -> dict[str, dict[str, Any]]:
    from engines.gdp_fetcher import G20_COUNTRIES
    result = {}
    for code in G20_COUNTRIES:
        s = _score(code)
        result[code] = {
            "risk_score":       s,
            "level":            _level(s),
            "trend":            _trend(code),
            "active_conflicts": _CONFLICTS.get(code, []),
            "military_rank":    _MILITARY.get(code, 30),
            "nuclear_status":   _NUCLEAR.get(code, 0),
            "alliance_score":   _ALLIANCE.get(code, 50),
        }
    return result


def get_risk_summary() -> dict[str, Any]:
    risks  = get_war_risk()
    scores = {k: v["risk_score"] for k, v in risks.items()}
    counts: dict[str, int] = {}
    for r in risks.values():
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    return {
        "highest_risk":   max(scores, key=scores.__getitem__),
        "lowest_risk":    min(scores, key=scores.__getitem__),
        "mean_score":     round(sum(scores.values()) / len(scores), 1),
        "level_counts":   counts,
        "critical_nations": [k for k, v in risks.items() if v["level"] == "CRITICAL"],
    }
