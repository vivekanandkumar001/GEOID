"""
engines/power_index.py
======================
Economic Power Index (EPI): composite score 0–100.

Components
----------
  GDP share (log-normalised)    55%
  GDP per capita (log-normalised) 20%
  Economic stability score      15%
  Trade openness proxy          10%

Public interface
----------------
    calculate_power_index(gdp_data)  -> dict[str, float]
    get_power_tier(score)            -> str
    get_power_index_full(gdp_data)   -> dict[str, dict]
"""

import math
from engines.economy_calc import calculate_gdp_per_capita

_W_GDP    = 0.55
_W_CAPITA = 0.20
_W_STAB   = 0.15
_W_TRADE  = 0.10

_STABILITY: dict[str, float] = {
    "US": 0.92, "CN": 0.72, "JP": 0.90, "DE": 0.93, "IN": 0.68,
    "GB": 0.87, "FR": 0.85, "BR": 0.62, "IT": 0.76, "CA": 0.91,
    "KR": 0.82, "AU": 0.94, "MX": 0.58, "ID": 0.63, "TR": 0.48,
    "SA": 0.65, "AR": 0.38, "ZA": 0.52, "RU": 0.28,
}

_TRADE: dict[str, float] = {
    "US": 0.60, "CN": 0.70, "JP": 0.62, "DE": 0.88, "IN": 0.55,
    "GB": 0.72, "FR": 0.70, "BR": 0.42, "IT": 0.74, "CA": 0.78,
    "KR": 0.90, "AU": 0.65, "MX": 0.80, "ID": 0.52, "TR": 0.68,
    "SA": 0.70, "AR": 0.38, "ZA": 0.62, "RU": 0.50,
}

_TIERS = [(80,"Superpower"),(60,"Major Power"),(40,"Significant"),(25,"Emerging"),(0,"Developing")]


def _log_norm(values: dict[str, float]) -> dict[str, float]:
    log_vals = {k: math.log1p(v) for k, v in values.items()}
    lo, hi = min(log_vals.values()), max(log_vals.values())
    spread = hi - lo or 1
    return {k: (v - lo) / spread for k, v in log_vals.items()}


def calculate_power_index(gdp_data: dict[str, float]) -> dict[str, float]:
    if not gdp_data:
        return {}
    gdp_norm  = _log_norm(gdp_data)
    cap_norm  = _log_norm(calculate_gdp_per_capita(gdp_data))
    raw = {
        code: (_W_GDP * gdp_norm.get(code, 0)
               + _W_CAPITA * cap_norm.get(code, 0)
               + _W_STAB * _STABILITY.get(code, 0.5)
               + _W_TRADE * _TRADE.get(code, 0.5))
        for code in gdp_data
    }
    top = max(raw.values()) or 1
    return {k: round(v / top * 100, 2) for k, v in raw.items()}


def get_power_tier(score: float) -> str:
    for threshold, label in _TIERS:
        if score >= threshold:
            return label
    return "Developing"


def get_power_index_full(gdp_data: dict[str, float]) -> dict[str, dict]:
    scores = calculate_power_index(gdp_data)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {
        code: {"score": score, "tier": get_power_tier(score), "rank": rank + 1}
        for rank, (code, score) in enumerate(ranked)
    }
