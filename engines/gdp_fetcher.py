"""
engines/gdp_fetcher.py
======================
Fetches GDP data for all G20 countries from the World Bank API.

Public interface
----------------
    get_gdp_data()        -> dict[str, float]   GDP in billion USD
    get_country_names()   -> dict[str, str]      ISO-2 -> display name
"""

import json
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country registry
# ---------------------------------------------------------------------------

G20_COUNTRIES: dict[str, str] = {
    "US": "United States",  "CN": "China",         "JP": "Japan",
    "DE": "Germany",        "IN": "India",          "GB": "United Kingdom",
    "FR": "France",         "BR": "Brazil",         "IT": "Italy",
    "CA": "Canada",         "KR": "South Korea",    "AU": "Australia",
    "MX": "Mexico",         "ID": "Indonesia",      "TR": "Turkey",
    "SA": "Saudi Arabia",   "AR": "Argentina",      "ZA": "South Africa",
    "RU": "Russia",
}

# ---------------------------------------------------------------------------
# Static fallback GDP values (billion USD, ~2024 estimates)
# Used when the World Bank API is unreachable.
# ---------------------------------------------------------------------------

FALLBACK_GDP: dict[str, float] = {
    "US": 27360.0, "CN": 17795.0, "JP":  4213.0, "DE":  4430.0,
    "IN":  3730.0, "GB":  3090.0, "FR":  2924.0, "BR":  2174.0,
    "IT":  2170.0, "CA":  2140.0, "KR":  1710.0, "AU":  1690.0,
    "MX":  1322.0, "ID":  1319.0, "TR":  1108.0, "SA":  1062.0,
    "AR":   621.0, "ZA":   377.0, "RU":  1862.0,
}

# ---------------------------------------------------------------------------
# Cache config
# ---------------------------------------------------------------------------

_CACHE_PATH    = os.path.join(os.path.dirname(__file__), "..", "data", "gdp_cache.json")
_CACHE_TTL     = int(os.getenv("GDP_CACHE_TTL", 3600))   # 1 hour
_REQUEST_TIMEOUT = 12

_WB_URL = (
    "https://api.worldbank.org/v2/country/"
    + ";".join(G20_COUNTRIES.keys())
    + "/indicator/NY.GDP.MKTP.CD"
)


# ---------------------------------------------------------------------------
# World Bank fetch
# ---------------------------------------------------------------------------

def _fetch_from_worldbank() -> Optional[dict[str, float]]:
    try:
        resp = requests.get(
            _WB_URL,
            params={"format": "json", "mrv": 1, "per_page": 100},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.warning("World Bank API error: %s", exc)
        return None

    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return None

    data: dict[str, float] = {}
    for rec in payload[1]:
        code = (rec.get("countryiso3166alpha2") or rec.get("country", {}).get("id", "")).upper()
        val  = rec.get("value")
        if code in G20_COUNTRIES and val is not None:
            data[code] = round(float(val) / 1e9, 2)

    return data if len(data) >= 10 else None


# ---------------------------------------------------------------------------
# Disk cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> Optional[dict[str, float]]:
    try:
        if not os.path.exists(_CACHE_PATH):
            return None
        with open(_CACHE_PATH, "r", encoding="utf-8") as fh:
            cache = json.load(fh)
        if time.time() - cache.get("timestamp", 0) < _CACHE_TTL:
            d = cache.get("data", {})
            if len(d) >= 10:
                return d
    except Exception:
        pass
    return None


def _save_cache(data: dict[str, float]) -> None:
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump({"timestamp": time.time(), "data": data}, fh, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_gdp_data() -> dict[str, float]:
    """
    Return GDP values (billion USD) for all 19 G20 countries.
    Resolution: disk cache → World Bank API → static fallback.
    """
    cached = _load_cache()
    if cached:
        return cached

    fetched = _fetch_from_worldbank()
    if fetched:
        _save_cache(fetched)
        return fetched

    logger.info("Using static fallback GDP data")
    fallback = dict(FALLBACK_GDP)
    _save_cache(fallback)
    return fallback


def get_country_names() -> dict[str, str]:
    """Return ISO-2 to display-name mapping for all G20 countries."""
    return dict(G20_COUNTRIES)
