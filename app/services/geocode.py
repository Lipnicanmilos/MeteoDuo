"""Geokódovanie názvov miest na súradnice cez Open-Meteo Geocoding API."""
import re

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# jednoduchá in-memory cache: city_name -> (lat, lon) | None
_cache: dict[str, tuple[float, float] | None] = {}


def _clean_name(name: str) -> str:
    """SHMU názvy typu 'Bardejov (centrum)' alebo 'Baranovo - Zadky' -> základ."""
    name = re.sub(r"\(.*?\)", "", name)
    name = name.split(" - ")[0]
    return name.strip()


async def geocode(client: httpx.AsyncClient, name: str) -> tuple[float, float] | None:
    key = name.lower()
    if key in _cache:
        return _cache[key]

    query = _clean_name(name)
    try:
        res = await client.get(
            GEOCODE_URL,
            params={"name": query, "count": 10, "language": "sk"},
            timeout=10,
        )
        res.raise_for_status()
        results = res.json().get("results") or []
    except httpx.HTTPError:
        return None  # neúspech necachujeme, skúsi sa nabudúce

    coords = None
    for r in results:
        if r.get("country_code") == "SK":
            coords = (r["latitude"], r["longitude"])
            break

    _cache[key] = coords
    return coords
