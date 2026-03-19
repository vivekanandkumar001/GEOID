"""
engines/gdp_forecast.py
=======================
Multi-year GDP forecast using linear regression on historical growth rates.
Projects up to FORECAST_YEARS ahead with geopolitical stress adjustment.

Public interface
----------------
    get_gdp_forecast(gdp_data) -> dict[str, dict]
"""

import logging
from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
from engines.gdp_fetcher import get_gdp_data
from engines.gdp_fetcher import fetch_gdp
logger = logging.getLogger(__name__)

FORECAST_YEARS = 3
BASE_YEAR      = 2025

# Historical annual growth rates % — World Bank WDI (2020-2024)
_GROWTH: dict[str, list] = {
    "US": [ 2.3,  5.9,  2.1,  2.5,  2.8], "CN": [ 2.2,  8.1,  3.0,  5.2,  5.1],
    "JP": [-4.1,  2.1,  1.0,  1.9,  1.5], "DE": [-3.8,  2.6,  1.8, -0.3,  0.9],
    "IN": [-6.6,  8.7,  7.0,  8.2,  6.8], "GB": [-11.0, 7.5,  4.1,  0.1,  1.2],
    "FR": [-7.5,  6.8,  2.5,  0.9,  1.4], "BR": [-3.9,  4.6,  2.9,  2.9,  3.2],
    "IT": [-9.0,  6.7,  3.7,  0.7,  1.0], "CA": [-5.1,  5.0,  3.4,  1.2,  1.6],
    "KR": [-0.7,  4.0,  2.6,  1.4,  2.3], "AU": [-2.2,  4.9,  3.7,  2.0,  1.8],
    "MX": [-8.2,  4.8,  3.9,  3.2,  2.8], "ID": [-2.1,  3.7,  5.3,  5.0,  5.2],
    "TR": [ 1.8, 11.4,  5.6,  4.5,  3.8], "SA": [-4.1,  3.9,  8.7,  0.8,  2.5],
    "AR": [-9.9, 10.7,  5.0, -2.5,  3.0], "ZA": [-6.4,  4.9,  1.9,  0.7,  1.2],
    "RU": [-2.7,  5.6, -2.1,  3.6,  2.4],
}

_STRESS: dict[str, float] = {
    "US": 0.98, "CN": 0.91, "JP": 0.97, "DE": 0.95, "IN": 1.04,
    "GB": 0.97, "FR": 0.96, "BR": 1.01, "IT": 0.95, "CA": 0.99,
    "KR": 0.97, "AU": 1.01, "MX": 0.99, "ID": 1.03, "TR": 0.92,
    "SA": 0.96, "AR": 0.88, "ZA": 0.97, "RU": 0.83,
}


def _project(rates: list, steps: int) -> list:
    n = len(rates)
    x = np.arange(n, dtype=float).reshape(-1, 1)
    x_aug = np.hstack([x, np.ones((n, 1))])
    y = np.array(rates, dtype=float)
    try:
        coeffs, *_ = np.linalg.lstsq(x_aug, y, rcond=None)
        slope, intercept = coeffs
    except np.linalg.LinAlgError:
        slope, intercept = 0.0, float(np.mean(y))
    return [float(slope * (n + i) + intercept) for i in range(steps)]


def get_gdp_forecast(gdp_data: dict[str, float]) -> dict[str, dict[str, Any]]:
    result = {}
    for code, current in gdp_data.items():
        hist    = _GROWTH.get(code, [2.0] * 5)
        stress  = _STRESS.get(code, 1.0)
        proj    = [r * stress for r in _project(hist, FORECAST_YEARS)]
        yearly  = {}
        gdp     = current
        for i, rate in enumerate(proj):
            gdp = gdp * (1.0 + rate / 100.0)
            yearly[str(BASE_YEAR + i)] = round(gdp, 2)
        avg  = round(float(np.mean(proj)), 3)
        vol  = round(float(np.std(hist)), 3)
        conf = round(max(30.0, min(92.0, 90.0 - vol * 3.5 - abs(avg) * 1.2)), 1)
        result[code] = {
            "current_gdp":        current,
            "forecast":           yearly,
            "avg_growth_pct":     avg,
            "growth_volatility":  vol,
            "confidence":         conf,
            "trend":              "↑" if avg > 0 else "↓",
            "stress_factor":      stress,
        }
    return result
