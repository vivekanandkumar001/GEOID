"""
GEOID — Global Economy Intelligence Operations Dashboard
engines/ package

Modules
-------
gdp_fetcher      World Bank API + TTL cache + fallback
economy_calc     GDP totals, shares, per-capita, ranks
power_index      Economic Power Index (composite 0-100)
war_risk         Geopolitical threat simulation
gdp_forecast     Multi-year linear regression forecast
ai_gdp_forecast  Ensemble ML forecast (poly + holt + ridge)
sector_data      GDP sector breakdowns per country
war_news         Intelligence headlines feed
"""
from engines.gdp_fetcher import fetch_gdp