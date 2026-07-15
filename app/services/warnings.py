"""Výstrahy počasia z Meteoalarm (zdroj: SHMÚ).

Meteoalarm publikuje výstrahy na úrovni okresov (EMMA_ID, napr. SK305 =
Partizánske). JSON API vracia pre každú výstrahu okres (areaDesc), typ,
farbu (awareness_level) a platnosť. Obec priraďujeme k okresu cez pole
`okres` v cities.json (predpočítané scripts/assign_okres.py).

Frontend potom pri obci zobrazí farebný prúžok, keď v jej okrese platí
(alebo o chvíľu začne) výstraha.
"""
import unicodedata
from datetime import datetime, timedelta, timezone

import httpx

FEED_URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-slovakia"

# awareness_level -> farba a slovenský názov úrovne (green sa nezobrazuje)
LEVELS = {
    "yellow": {"color": "#eab308", "label": "žltá"},
    "orange": {"color": "#f97316", "label": "oranžová"},
    "red":    {"color": "#dc2626", "label": "červená"},
}
LEVEL_RANK = {"yellow": 1, "orange": 2, "red": 3}

# awareness_type -> ikona + slovenský názov javu
TYPES = {
    "1": ("💨", "vietor"),
    "2": ("❄️", "sneh/poľadovica"),
    "3": ("⛈️", "búrky"),
    "4": ("🌫️", "hmla"),
    "5": ("🌡️", "vysoké teploty"),
    "6": ("🥶", "nízke teploty"),
    "7": ("🌊", "pobrežné javy"),
    "8": ("🔥", "lesné požiare"),
    "9": ("🏔️", "lavíny"),
    "10": ("🌧️", "dážď"),
    "11": ("⚡", "iné"),
    "12": ("🌊", "povodne"),
    "13": ("🌊", "prívalová povodeň"),
}

# cache celého feedu: (expires_utc, {norm_okres: [warning, ...]})
_cache: tuple[datetime, dict] | None = None
CACHE_TTL = timedelta(minutes=10)


def norm_okres(name: str) -> str:
    """'Okres Námestovo' / 'Námestovo' -> 'namestovo' (bez diakritiky, lower)."""
    if not name:
        return ""
    s = name.strip()
    if s.lower().startswith("okres "):
        s = s[6:]
    return (unicodedata.normalize("NFD", s)
            .encode("ascii", "ignore").decode().lower().strip())


def _pick_info(infos: list[dict]) -> dict | None:
    """Uprednostni slovenský jazyk, inak prvý dostupný."""
    for i in infos:
        if (i.get("language") or "").lower().startswith("sk"):
            return i
    return infos[0] if infos else None


def _parse_params(params: list[dict]) -> tuple[str | None, str | None]:
    """Z parametrov vytiahne (farba, typ_id). awareness_level='2; yellow; Moderate'."""
    color = type_id = None
    for p in params or []:
        val = p.get("value", "")
        if p.get("valueName") == "awareness_level":
            parts = [x.strip() for x in val.split(";")]
            if len(parts) >= 2:
                color = parts[1].lower()
        elif p.get("valueName") == "awareness_type":
            parts = [x.strip() for x in val.split(";")]
            if parts and parts[0].isdigit():
                type_id = parts[0]
    return color, type_id


def _digest(feed: dict) -> dict:
    """Feed -> {norm_okres: [ {color,label,icon,type,event,headline,onset,expires} ]}."""
    now = datetime.now(timezone.utc)
    by_okres: dict[str, list] = {}

    for w in feed.get("warnings", []):
        alert = w.get("alert", {})
        info = _pick_info(alert.get("info", []))
        if not info:
            continue

        color, type_id = _parse_params(info.get("parameter", []))
        if color not in LEVELS:      # green / neznáme -> nezobrazujeme
            continue

        expires = _parse_dt(info.get("expires"))
        if expires and expires < now:
            continue                 # už neplatná

        icon, type_name = TYPES.get(type_id, ("⚠️", "výstraha"))
        warning = {
            "color": LEVELS[color]["color"],
            "level": LEVELS[color]["label"],
            "rank": LEVEL_RANK[color],
            "icon": icon,
            "type": type_name,
            "event": info.get("event"),
            "headline": info.get("headline"),
            "onset": info.get("onset"),
            "expires": info.get("expires"),
        }

        for area in info.get("area", []):
            key = norm_okres(area.get("areaDesc", ""))
            if key:
                by_okres.setdefault(key, []).append(warning)

    # v rámci okresu zoradiť podľa závažnosti (najhoršia prvá) a deduplikovať
    for key, lst in by_okres.items():
        seen = set()
        uniq = []
        for wn in sorted(lst, key=lambda x: -x["rank"]):
            sig = (wn["type"], wn["level"], wn["onset"], wn["expires"])
            if sig not in seen:
                seen.add(sig)
                uniq.append(wn)
        by_okres[key] = uniq

    return by_okres


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Meteoalarm dáva napr. '2026-07-17T16:00:00-00:00'
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


async def fetch_all(client: httpx.AsyncClient) -> dict:
    """Vráti {norm_okres: [warnings]} pre celé SK. Cachované ~10 min."""
    global _cache
    now = datetime.now(timezone.utc)
    if _cache and _cache[0] > now:
        return _cache[1]

    res = await client.get(FEED_URL, timeout=15)
    res.raise_for_status()
    data = _digest(res.json())
    _cache = (now + CACHE_TTL, data)
    return data


async def for_okres(client: httpx.AsyncClient, okres: str | None) -> list[dict]:
    """Výstrahy pre daný okres (názov z cities.json). Prázdny zoznam ak žiadne."""
    if not okres:
        return []
    return (await fetch_all(client)).get(norm_okres(okres), [])
