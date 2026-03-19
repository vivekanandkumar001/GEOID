"""
engines/economy_calc.py
=======================
Core economic calculations on raw GDP data.

Public interface
----------------
    calculate_total_gdp(gdp_data)      -> float
    calculate_gdp_share(gdp_data)      -> dict[str, float]
    calculate_gdp_per_capita(gdp_data) -> dict[str, float]
    calculate_gdp_rank(gdp_data)       -> dict[str, int]
    calculate_summary_stats(gdp_data)  -> dict
"""

import statistics
from typing import Any
from engines.gdp_fetcher import get_gdp_data
from engines.gdp_fetcher import fetch_gdp
# Population estimates (millions, ~2024)
_POP: dict[str, float] = {
    "US": 335.0, "CN": 1410.0, "JP":  124.0, "DE":   84.0,
    "IN": 1430.0, "GB":   68.0, "FR":   68.0, "BR":  215.0,
    "IT":   59.0, "CA":   40.0, "KR":   52.0, "AU":   27.0,
    "MX":  130.0, "ID":  278.0, "TR":   85.0, "SA":   36.0,
    "AR":   46.0, "ZA":   60.0, "RU":  145.0,
}


def calculate_total_gdp(gdp_data: dict[str, float]) -> float:
    return round(sum(gdp_data.values()), 2)


def calculate_gdp_share(gdp_data: dict[str, float]) -> dict[str, float]:
    total = calculate_total_gdp(gdp_data) or 1
    return {k: round(v / total * 100, 4) for k, v in gdp_data.items()}


def calculate_gdp_per_capita(gdp_data: dict[str, float]) -> dict[str, float]:
    return {
        code: round(gdp / _POP.get(code, 50.0), 2)
        for code, gdp in gdp_data.items()
    }


def calculate_gdp_rank(gdp_data: dict[str, float]) -> dict[str, int]:
    ranked = sorted(gdp_data, key=gdp_data.__getitem__, reverse=True)
    return {code: i + 1 for i, code in enumerate(ranked)}


def calculate_summary_stats(gdp_data: dict[str, float]) -> dict[str, Any]:
    if not gdp_data:
        return {}
    vals = list(gdp_data.values())
    return {
        "total_gdp":        round(sum(vals), 2),
        "mean_gdp":         round(statistics.mean(vals), 2),
        "median_gdp":       round(statistics.median(vals), 2),
        "largest_economy":  max(gdp_data, key=gdp_data.__getitem__),
        "smallest_economy": min(gdp_data, key=gdp_data.__getitem__),
        "top_gdp":          round(max(vals), 2),
        "bottom_gdp":       round(min(vals), 2),
        "std_deviation":    round(statistics.stdev(vals) if len(vals) > 1 else 0, 2),
        "country_count":    len(vals),
    }
