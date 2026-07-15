"""Meteogramy zo SHMÚ (www.shmu.sk).

Každá stránka obsahuje zoznam vygenerovaných meteogramov; img_files[0] je
najnovší. Obrázok proxujeme cez backend (žiadne CORS/hotlink problémy na
frontende). Podporované typy: aladin (3 dni), laef (ansámbel A-LAEF, 3 dni),
egram8 (ansámbel ECMWF, 8 dní), mgram10 (ECMWF, 10 dní).
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

SHMU_BASE = "https://www.shmu.sk"
PAGE_URLS = {
    "aladin":  SHMU_BASE + "/sk/?page=769&nwp_mesto={city_id}",
    "laef":    SHMU_BASE + "/sk/?page=1&id=meteo_num_laef_egram&nwp_mesto={city_id}",
    "egram8":  SHMU_BASE + "/sk/?page=1&id=meteo_num_egram8&nwp_mesto={city_id}",
    "mgram10": SHMU_BASE + "/sk/?page=1&id=meteo_num_mgram10&nwp_mesto={city_id}",
}
METEOGRAM_TYPES = frozenset(PAGE_URLS)
IMG_RE = re.compile(r'img_files\[0\]="([^"]+)"')

CITIES_FILE = Path(__file__).resolve().parent.parent / "data" / "cities.json"
CITIES: list[dict] = json.loads(CITIES_FILE.read_text(encoding="utf-8"))
CITY_IDS = {c["id"] for c in CITIES}
CITY_NAMES = {c["id"]: c["name"] for c in CITIES}
# predpočítané skriptom scripts/geocode_cities.py; pár bodov súradnice nemá
CITY_COORDS = {c["id"]: (c["lat"], c["lon"])
               for c in CITIES if c.get("lat") is not None}

# cache: (city_id, mg_type) -> (expires_utc, image_url)
_url_cache: dict[tuple[str, str], tuple[datetime, str]] = {}
URL_TTL = timedelta(minutes=10)


async def latest_meteogram_url(client: httpx.AsyncClient, city_id: str,
                               mg_type: str = "aladin") -> str | None:
    now = datetime.now(timezone.utc)
    key = (city_id, mg_type)
    cached = _url_cache.get(key)
    if cached and cached[0] > now:
        return cached[1]

    res = await client.get(PAGE_URLS[mg_type].format(city_id=city_id), timeout=15)
    res.raise_for_status()
    m = IMG_RE.search(res.text)
    if not m:
        return None

    url = SHMU_BASE + m.group(1)
    _url_cache[key] = (now + URL_TTL, url)
    return url


async def fetch_meteogram_png(client: httpx.AsyncClient, city_id: str,
                              mg_type: str = "aladin") -> bytes | None:
    url = await latest_meteogram_url(client, city_id, mg_type)
    if not url:
        return None
    res = await client.get(url, timeout=20)
    res.raise_for_status()
    return res.content
