"""Meteogram ALADIN zo SHMÚ (www.shmu.sk).

Stránka ?page=769&nwp_mesto=<id> obsahuje zoznam vygenerovaných meteogramov;
img_files[0] je najnovší. Obrázok proxujeme cez backend (žiadne CORS/hotlink
problémy na frontende).
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

SHMU_BASE = "https://www.shmu.sk"
PAGE_URL = SHMU_BASE + "/sk/?page=769&nwp_mesto={city_id}"
IMG_RE = re.compile(r'img_files\[0\]="([^"]+)"')

CITIES_FILE = Path(__file__).resolve().parent.parent / "data" / "cities.json"
CITIES: list[dict] = json.loads(CITIES_FILE.read_text(encoding="utf-8"))
CITY_IDS = {c["id"] for c in CITIES}
CITY_NAMES = {c["id"]: c["name"] for c in CITIES}

# cache: city_id -> (expires_utc, image_url)
_url_cache: dict[str, tuple[datetime, str]] = {}
URL_TTL = timedelta(minutes=10)


async def latest_meteogram_url(client: httpx.AsyncClient, city_id: str) -> str | None:
    now = datetime.now(timezone.utc)
    cached = _url_cache.get(city_id)
    if cached and cached[0] > now:
        return cached[1]

    res = await client.get(PAGE_URL.format(city_id=city_id), timeout=15)
    res.raise_for_status()
    m = IMG_RE.search(res.text)
    if not m:
        return None

    url = SHMU_BASE + m.group(1)
    _url_cache[city_id] = (now + URL_TTL, url)
    return url


async def fetch_meteogram_png(client: httpx.AsyncClient, city_id: str) -> bytes | None:
    url = await latest_meteogram_url(client, city_id)
    if not url:
        return None
    res = await client.get(url, timeout=20)
    res.raise_for_status()
    return res.content
