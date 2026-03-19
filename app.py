"""
app.py
======
GEOID — Global Economy Intelligence Operations Dashboard
Flask application entry point.

Routes
------
GET /              Serves the dashboard HTML
GET /api/economy   Full intelligence payload (JSON)
GET /api/forecast  AI-only forecast endpoint (JSON)
GET /api/health    Liveness probe

Run
---
    python app.py
    gunicorn -w 4 -b 0.0.0.0:5000 app:app   # production
"""

import logging
import os
import time
from typing import Any

from flask import Flask, jsonify, render_template, Response

from engines.gdp_fetcher     import get_gdp_data, get_country_names
from engines.economy_calc    import (
    calculate_total_gdp, calculate_gdp_share,
    calculate_gdp_per_capita, calculate_gdp_rank, calculate_summary_stats,
)
from engines.power_index     import get_power_index_full
from engines.war_risk        import get_war_risk, get_risk_summary
from engines.gdp_forecast    import get_gdp_forecast
from engines.ai_gdp_forecast import run_ai_forecast, get_forecast_summary
from engines.sector_data     import get_sector_importance
from engines.war_news        import get_war_news

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.after_request
def cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


# ---------------------------------------------------------------------------
# Payload cache
# ---------------------------------------------------------------------------

_cache:    dict[str, Any] = {}
_cache_ts: float          = 0.0
_CACHE_TTL = float(os.getenv("PAYLOAD_CACHE_TTL", 15))


def _build_payload() -> dict[str, Any]:
    global _cache, _cache_ts
    now = time.time()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache

    logger.info("Building fresh economy payload")
    t0 = time.perf_counter()

    # 1. GDP (source of truth)
    gdp_data      = get_gdp_data()
    country_names = get_country_names()

    # 2. Economic calculations
    total_gdp      = calculate_total_gdp(gdp_data)
    gdp_share      = calculate_gdp_share(gdp_data)
    gdp_per_capita = calculate_gdp_per_capita(gdp_data)
    gdp_rank       = calculate_gdp_rank(gdp_data)
    summary_stats  = calculate_summary_stats(gdp_data)

    # 3. Power index
    power_index = get_power_index_full(gdp_data)

    # 4. War risk
    war_risk     = get_war_risk()
    risk_summary = get_risk_summary()

    # 5. Multi-year forecast
    gdp_forecast = get_gdp_forecast(gdp_data)

    # 6. AI ensemble forecast
    ai_forecast         = run_ai_forecast(gdp_data)
    ai_forecast_summary = get_forecast_summary(gdp_data)

    # 7. Sectors
    sector_data = get_sector_importance()

    # 8. News
    war_news = get_war_news(count=8)

    elapsed = time.perf_counter() - t0
    logger.info("Payload built in %.3fs", elapsed)

    payload: dict[str, Any] = {
        "gdp":                  gdp_data,
        "gdp_share":            gdp_share,
        "gdp_per_capita":       gdp_per_capita,
        "gdp_rank":             gdp_rank,
        "total_g20_gdp":        total_gdp,
        "country_names":        country_names,
        "summary_stats":        summary_stats,
        "power_index":          power_index,
        "war_risk":             war_risk,
        "risk_summary":         risk_summary,
        "gdp_forecast":         gdp_forecast,
        "ai_forecast":          ai_forecast,
        "ai_forecast_summary":  ai_forecast_summary,
        "sector_importance":    sector_data,
        "war_news":             war_news,
        "meta": {
            "timestamp":        now,
            "build_time_ms":    round(elapsed * 1000, 1),
            "country_count":    len(gdp_data),
            "data_year":        2024,
            "unit":             "Billion USD",
            "cache_ttl":        _CACHE_TTL,
            "ai_model_version": ai_forecast_summary.get("model_version", "—"),
        },
    }
    _cache    = payload
    _cache_ts = now
    return payload


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/economy")
def economy() -> Response:
    """
    GET /api/economy — full intelligence payload.

    ai_forecast shape per country:
      next_year_gdp, next_year_growth, confidence_interval [lo,hi],
      model_breakdown {poly_regression, exponential_smoothing, ridge_features},
      confidence_score, signal, geo_risk_factor, model_version
    """
    try:
        return jsonify(_build_payload())
    except Exception as exc:
        logger.exception("Payload build failed: %s", exc)
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500


@app.route("/api/forecast")
def forecast_only() -> Response:
    """GET /api/forecast — AI forecast data only."""
    try:
        gdp     = get_gdp_data()
        ai      = run_ai_forecast(gdp)
        summary = get_forecast_summary(gdp)
        return jsonify({"ai_forecast": ai, "ai_forecast_summary": summary,
                        "timestamp": time.time()})
    except Exception as exc:
        logger.exception("Forecast endpoint error: %s", exc)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/health")
def health() -> Response:
    return jsonify({"status": "ok", "ts": time.time(),
                    "uptime": round(time.time() - _START, 1)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return "GEOID Running"


_START = time.time()

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    host  = os.getenv("HOST",  "0.0.0.0")
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    logger.info("=" * 60)
    logger.info("  GEOID — Global Economy Intelligence Dashboard")
    logger.info("  http://%s:%d", host, port)
    logger.info("=" * 60)
    app.run(debug=debug, host=host, port=port)
