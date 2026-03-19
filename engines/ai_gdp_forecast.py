"""
engines/ai_gdp_forecast.py
==========================
AI GDP Forecasting — Ensemble of three ML models:
  1. Polynomial Regression (degree 2, Ridge regularised)
  2. Holt's Double Exponential Smoothing
  3. Ridge Regression with engineered features

Final prediction = weighted ensemble (poly 30% + holt 25% + ridge 45%)
adjusted by per-country geopolitical stress multiplier.

Public interface
----------------
    run_ai_forecast(gdp_data)          -> dict[str, dict]
    get_next_year_predictions(gdp_data) -> dict[str, float]
    get_forecast_summary(gdp_data)     -> dict
"""

import logging
from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

MODEL_VERSION = "GEOID-ML-3.1-ENSEMBLE"

# Historical GDP (billion USD) 2015–2024, 10 data points
_HIST: dict[str, list] = {
    "US": [18206,18695,19477,20533,21381,20893,23315,25744,27357,27360],
    "CN": [ 9181,10166,11795,13608,14343,14688,17734,17963,17786,17795],
    "JP": [ 4395, 4923, 4859, 5042, 5118, 4975, 4940, 4232, 4213, 4213],
    "DE": [ 3357, 3479, 3693, 3968, 3888, 3884, 4260, 4082, 4430, 4430],
    "IN": [ 2089, 2295, 2651, 2702, 2869, 2671, 3150, 3385, 3730, 3730],
    "GB": [ 2897, 2678, 2637, 2862, 2830, 2764, 3131, 3071, 3090, 3090],
    "FR": [ 2438, 2471, 2590, 2778, 2716, 2639, 2957, 2781, 2924, 2924],
    "BR": [ 1802, 1797, 2063, 1916, 1874, 1445, 1649, 1920, 2174, 2174],
    "IT": [ 1828, 1870, 1961, 2091, 2004, 1897, 2107, 2011, 2170, 2170],
    "CA": [ 1558, 1528, 1648, 1722, 1741, 1643, 1988, 2140, 2140, 2140],
    "KR": [ 1383, 1415, 1531, 1619, 1647, 1631, 1799, 1673, 1710, 1710],
    "AU": [ 1348, 1205, 1323, 1436, 1396, 1330, 1542, 1680, 1690, 1690],
    "MX": [ 1170, 1078, 1158, 1221, 1269, 1086, 1293, 1273, 1322, 1322],
    "ID": [  861,  932, 1015, 1042, 1119, 1059, 1186, 1319, 1319, 1319],
    "TR": [  860,  863,  858,  771,  761,  720,  819,  906, 1108, 1108],
    "SA": [  653,  644,  683,  786,  793,  700,  834,  934, 1062, 1062],
    "AR": [  635,  545,  644,  519,  449,  385,  487,  632,  621,  621],
    "ZA": [  317,  296,  349,  368,  352,  302,  420,  405,  377,  377],
    "RU": [ 1363, 1283, 1578, 1658, 1700, 1481, 1776, 2244, 1862, 1862],
}

_GEO: dict[str, float] = {
    "US": 0.98, "CN": 0.91, "JP": 0.97, "DE": 0.95, "IN": 1.03,
    "GB": 0.97, "FR": 0.96, "BR": 1.01, "IT": 0.95, "CA": 0.99,
    "KR": 0.97, "AU": 1.01, "MX": 0.99, "ID": 1.03, "TR": 0.92,
    "SA": 0.96, "AR": 0.88, "ZA": 0.97, "RU": 0.83,
}

_SIGNALS = [(4.0,"EXPANSION"),(1.0,"STABLE"),(-1.0,"CONTRACTION"),(-999,"RECESSION")]


def _signal(pct: float) -> str:
    for t, l in _SIGNALS:
        if pct >= t: return l
    return "RECESSION"


# ── Model 1: Polynomial regression ──────────────────────────────────────────

def _poly_predict(series: list, target_x: float) -> float:
    x = np.arange(len(series), dtype=float).reshape(-1, 1)
    y = np.array(series, dtype=float)
    model = Pipeline([
        ("poly",   PolynomialFeatures(degree=2, include_bias=True)),
        ("scaler", StandardScaler()),
        ("ridge",  Ridge(alpha=5.0)),
    ])
    model.fit(x, y)
    pred = model.predict(np.array([[target_x]]))[0]
    return float(max(pred, y[-1] * 0.5))


# ── Model 2: Holt's double exponential smoothing ─────────────────────────────

def _holt_predict(series: list, alpha: float = 0.35, beta: float = 0.25) -> float:
    if len(series) < 2: return float(series[-1])
    level = float(series[0])
    trend = float(series[1] - series[0])
    for t in range(1, len(series)):
        prev  = level
        level = alpha * series[t] + (1 - alpha) * (level + trend)
        trend = beta  * (level - prev) + (1 - beta) * trend
    return float(level + trend)


# ── Model 3: Ridge regression with engineered features ──────────────────────

def _ridge_predict(series: list, geo: float) -> float:
    s = np.array(series, dtype=float)
    n = len(s)
    rows_x, rows_y = [], []
    for i in range(3, n):
        cur  = s[i-1]; prev1 = s[i-2]
        prev3 = s[i-4] if i >= 4 else s[0]
        cagr = (cur/prev3)**(1/3)-1 if prev3>0 else 0
        g1   = (cur-prev1)/prev1 if prev1>0 else 0
        rel  = cur/max(s)
        rows_x.append([cur, cagr, g1, rel, geo])
        rows_y.append(s[i])
    if not rows_x: return float(s[-1])
    X  = np.array(rows_x); y = np.array(rows_y)
    sc = StandardScaler(); Xs = sc.fit_transform(X)
    rg = Ridge(alpha=2.0); rg.fit(Xs, y)
    cur  = s[-1]; prev1 = s[-2]; prev3 = s[-4] if n>=4 else s[0]
    cagr = (cur/prev3)**(1/3)-1 if prev3>0 else 0
    g1   = (cur-prev1)/prev1 if prev1>0 else 0
    rel  = cur/max(s)
    pred = float(rg.predict(sc.transform([[cur,cagr,g1,rel,geo]]))[0])
    return max(pred, cur*0.5)


# ── Ensemble ─────────────────────────────────────────────────────────────────

def _ensemble(series: list, geo: float) -> dict:
    n  = len(series)
    tx = float(n)
    p_poly  = float(np.clip(_poly_predict(series, tx),  series[-1]*0.6, series[-1]*1.4))
    p_holt  = float(np.clip(_holt_predict(series),      series[-1]*0.6, series[-1]*1.4))
    p_ridge = float(np.clip(_ridge_predict(series, geo), series[-1]*0.6, series[-1]*1.4))
    ens     = (0.30*p_poly + 0.25*p_holt + 0.45*p_ridge) * geo
    spread  = max([p_poly,p_holt,p_ridge]) - min([p_poly,p_holt,p_ridge])
    ci_h    = max(spread*0.6, series[-1]*0.015)
    vol_pct = spread/series[-1]*100 if series[-1]>0 else 10
    conf    = round(max(30.0, min(98.0, 95 - vol_pct*2.5)), 1)
    return {
        "ensemble":  round(ens, 2),
        "ci_lower":  round(ens - ci_h, 2),
        "ci_upper":  round(ens + ci_h, 2),
        "conf":      conf,
        "breakdown": {
            "poly_regression":       round(p_poly,  2),
            "exponential_smoothing": round(p_holt,  2),
            "ridge_features":        round(p_ridge, 2),
        },
    }


# ── Public interface ─────────────────────────────────────────────────────────

def run_ai_forecast(gdp_data: dict[str, float]) -> dict[str, dict]:
    result = {}
    for code, current in gdp_data.items():
        hist = list(_HIST.get(code, [current]*10))
        hist[-1] = current   # anchor to live data
        geo  = _GEO.get(code, 1.0)
        try:
            ens = _ensemble(hist, geo)
        except Exception as exc:
            logger.warning("Ensemble failed for %s: %s", code, exc)
            ens = {
                "ensemble":  round(current*(1+0.02*geo), 2),
                "ci_lower":  round(current*0.97, 2),
                "ci_upper":  round(current*1.05, 2),
                "conf":      40.0,
                "breakdown": {"poly_regression":current,"exponential_smoothing":current,"ridge_features":current},
            }
        next_gdp = ens["ensemble"]
        yoy      = round((next_gdp - current)/current*100, 3) if current else 0
        result[code] = {
            "country_code":         code,
            "current_gdp":          current,
            "next_year_gdp":        next_gdp,
            "next_year_growth":     yoy,
            "confidence_interval":  [ens["ci_lower"], ens["ci_upper"]],
            "model_breakdown":      ens["breakdown"],
            "confidence_score":     ens["conf"],
            "signal":               _signal(yoy),
            "geo_risk_factor":      geo,
            "model_version":        MODEL_VERSION,
        }
    return result


def get_next_year_predictions(gdp_data: dict[str, float]) -> dict[str, float]:
    return {k: v["next_year_gdp"] for k, v in run_ai_forecast(gdp_data).items()}


def get_forecast_summary(gdp_data: dict[str, float]) -> dict:
    full     = run_ai_forecast(gdp_data)
    by_growth = sorted(full.items(), key=lambda x: x[1]["next_year_growth"], reverse=True)
    total_p  = sum(v["next_year_gdp"]  for v in full.values())
    total_c  = sum(v["current_gdp"]    for v in full.values())
    avg_g    = (total_p - total_c)/total_c*100 if total_c else 0
    return {
        "fastest_growing":      by_growth[0][0]  if by_growth else "—",
        "biggest_contraction":  by_growth[-1][0] if by_growth else "—",
        "avg_world_growth_pct": round(avg_g, 3),
        "expansion_count":      sum(1 for v in full.values() if v["signal"] in ("EXPANSION","STABLE")),
        "contraction_count":    sum(1 for v in full.values() if v["signal"] in ("CONTRACTION","RECESSION")),
        "total_predicted_gdp":  round(total_p, 2),
        "model_version":        MODEL_VERSION,
    }
