"""
engines/sector_data.py
======================
Economic sector breakdowns for each G20 country (% of GDP).
Based on World Bank national accounts & OECD sectoral statistics, 2023-2024.

Public interface
----------------
    get_sector_importance()               -> dict[str, dict[str, float]]
    get_country_sectors(code)             -> dict[str, float]
    get_dominant_sector(code)             -> str | None
    get_sector_gdp_values(code, gdp_data) -> dict[str, float]
"""

from typing import Optional
from engines.gdp_fetcher import get_gdp_data
from engines.gdp_fetcher import fetch_gdp
_DATA: dict[str, dict[str, float]] = {
    "US": {"Finance & Insurance":21,"Technology":18,"Healthcare":14,"Manufacturing":11,"Energy":8,"Real Estate":9,"Government":12,"Agriculture":1,"Other Services":6},
    "CN": {"Manufacturing":27,"Real Estate":13,"Finance":16,"Technology":14,"Energy":9,"Agriculture":7,"Construction":8,"Other Services":6},
    "JP": {"Manufacturing":21,"Finance":18,"Technology":15,"Services":20,"Healthcare":10,"Energy":6,"Agriculture":2,"Other":8},
    "DE": {"Manufacturing":23,"Automotive":12,"Finance":15,"Technology":13,"Healthcare":12,"Energy":10,"Agriculture":2,"Other Services":13},
    "IN": {"Services":22,"Technology":16,"Agriculture":15,"Manufacturing":14,"Finance":13,"Energy":10,"Construction":6,"Healthcare":4},
    "GB": {"Finance":26,"Services":22,"Technology":16,"Healthcare":13,"Manufacturing":10,"Energy":8,"Real Estate":4,"Agriculture":1},
    "FR": {"Services":24,"Finance":20,"Manufacturing":14,"Technology":13,"Healthcare":12,"Energy":9,"Agriculture":5,"Tourism":3},
    "BR": {"Agriculture":24,"Energy":18,"Manufacturing":16,"Services":18,"Finance":12,"Mining":8,"Technology":4},
    "IT": {"Manufacturing":20,"Services":22,"Finance":17,"Tourism":13,"Agriculture":8,"Technology":10,"Energy":10},
    "CA": {"Energy":22,"Finance":20,"Manufacturing":14,"Services":20,"Mining":10,"Agriculture":7,"Technology":7},
    "KR": {"Technology":25,"Manufacturing":22,"Finance":16,"Services":18,"Energy":9,"Agriculture":2,"Healthcare":8},
    "AU": {"Mining":28,"Finance":18,"Services":18,"Agriculture":12,"Energy":11,"Manufacturing":7,"Technology":6},
    "MX": {"Manufacturing":22,"Energy":18,"Agriculture":14,"Services":18,"Finance":14,"Mining":8,"Technology":6},
    "ID": {"Agriculture":22,"Manufacturing":19,"Energy":16,"Mining":12,"Services":16,"Finance":10,"Technology":5},
    "TR": {"Services":22,"Manufacturing":20,"Agriculture":18,"Finance":14,"Energy":12,"Tourism":8,"Technology":6},
    "SA": {"Energy & Oil":42,"Finance":16,"Services":14,"Manufacturing":12,"Mining":8,"Agriculture":4,"Technology":4},
    "AR": {"Agriculture":28,"Manufacturing":18,"Energy":16,"Services":16,"Finance":12,"Mining":6,"Technology":4},
    "ZA": {"Mining":24,"Finance":20,"Manufacturing":14,"Services":18,"Agriculture":12,"Energy":8,"Technology":4},
    "RU": {"Energy & Gas":38,"Manufacturing":16,"Finance":14,"Mining":12,"Agriculture":10,"Services":8,"Technology":2},
}


def get_sector_importance() -> dict[str, dict[str, float]]:
    return dict(_DATA)


def get_country_sectors(code: str) -> dict[str, float]:
    return dict(_DATA.get(code.upper(), {}))


def get_dominant_sector(code: str) -> Optional[str]:
    s = get_country_sectors(code)
    return max(s, key=s.__getitem__) if s else None


def get_sector_gdp_values(code: str, gdp_data: dict[str, float]) -> dict[str, float]:
    sectors   = get_country_sectors(code)
    total_gdp = gdp_data.get(code, 0.0)
    return {sector: round(pct / 100.0 * total_gdp, 2) for sector, pct in sectors.items()}
