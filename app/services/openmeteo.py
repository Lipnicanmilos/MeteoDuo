"""Číselné modely cez Open-Meteo pre porovnávaciu tabuľku.

Jedným requestom ťaháme viac modelov naraz (hourly premenné majú v odpovedi
príponu modelu). ECMWF zodpovedá tomu, čo predvolene zobrazuje Windy aj
10-dňový meteogram SHMÚ; ICON (DWD) a GFS (NOAA) sú ďalšie nezávislé modely.
ALADIN čísla SHMÚ nezverejňuje (len PNG meteogramy).

Denné súhrny majú rovnaký tvar ako yr.py: date/temp_min/temp_max/precip/
wind_max/wmo.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx

OM_URL = "https://api.open-meteo.com/v1/forecast"

# kľúč -> názov modelu v Open-Meteo API; poradie = poradie riadkov v tabuľke
MODELS = {
    "ecmwf": "ecmwf_ifs025",
    "icon": "icon_seamless",
    "gfs": "gfs_seamless",
}
HOURLY_VARS = ["temperature_2m", "precipitation", "wind_speed_10m", "weather_code"]
DAILY_VARS = ["sunrise", "sunset", "uv_index_max"]

# cache: (lat, lon) -> (expires_utc, payload)
_cache: dict[tuple[float, float], tuple[datetime, dict]] = {}
# cache pre denné údaje (slnko/UV) — vlastný request s lokálnym časom
_daily_cache: dict[tuple[float, float], tuple[datetime, list]] = {}
CACHE_TTL = timedelta(minutes=15)
FORECAST_DAYS = 10


async def fetch_forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Vráti {model_key: [denné súhrny]} pre všetky MODELS (UTC dni, ako yr.py)."""
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc)
    cached = _cache.get(key)
    if cached and cached[0] > now:
        return cached[1]

    res = await client.get(
        OM_URL,
        params={
            "latitude": key[0],
            "longitude": key[1],
            "hourly": ",".join(HOURLY_VARS),
            "models": ",".join(MODELS.values()),
            "wind_speed_unit": "ms",       # ako yr.no
            "timezone": "UTC",             # rovnaké hranice dní ako yr.py
            "forecast_days": FORECAST_DAYS,
        },
        timeout=20,
    )
    res.raise_for_status()
    hourly = res.json().get("hourly", {})

    payload = {mkey: _digest_model(hourly, mname) for mkey, mname in MODELS.items()}
    _cache[key] = (now + CACHE_TTL, payload)
    return payload


async def fetch_daily(client: httpx.AsyncClient, lat: float, lon: float) -> list[dict]:
    """Denné údaje: východ/západ slnka a max. UV index.

    Vlastný request s timezone=auto — slnko a UV chceme v lokálnom čase obce
    (modelové porovnanie naopak beží v UTC kvôli zhode hraníc dní s yr.py).
    Vracia [{date, sunrise, sunset, uv_max}] (ISO časy v lokálnom čase).
    """
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc)
    cached = _daily_cache.get(key)
    if cached and cached[0] > now:
        return cached[1]

    res = await client.get(
        OM_URL,
        params={
            "latitude": key[0],
            "longitude": key[1],
            "daily": ",".join(DAILY_VARS),
            "timezone": "auto",
            "forecast_days": FORECAST_DAYS,
        },
        timeout=20,
    )
    res.raise_for_status()
    d = res.json().get("daily", {})
    dates = d.get("time", [])
    sunrise = d.get("sunrise", [])
    sunset = d.get("sunset", [])
    uv = d.get("uv_index_max", [])

    out = []
    for i, date in enumerate(dates):
        out.append({
            "date": date,
            "sunrise": sunrise[i] if i < len(sunrise) else None,
            "sunset": sunset[i] if i < len(sunset) else None,
            "uv_max": round(uv[i], 1) if i < len(uv) and uv[i] is not None else None,
        })

    _daily_cache[key] = (now + CACHE_TTL, out)
    return out


def _digest_model(h: dict, model: str) -> list[dict]:
    times = h.get("time", [])

    def arr(var: str) -> list:
        # pri viacerých modeloch má premenná príponu, pri jednom nie
        return h.get(f"{var}_{model}") or h.get(var) or []

    temps, precs, winds, codes = (arr(v) for v in HOURLY_VARS)

    days: dict[str, dict] = {}
    for i, t in enumerate(times):
        day = t[:10]
        d = days.setdefault(day, {"date": day, "temps": [], "precip": 0.0,
                                  "winds": [], "day_codes": [], "all_codes": []})
        if i < len(temps) and temps[i] is not None:
            d["temps"].append(temps[i])
        if i < len(precs) and precs[i] is not None:
            d["precip"] += precs[i]
        if i < len(winds) and winds[i] is not None:
            d["winds"].append(winds[i])
        if i < len(codes) and codes[i] is not None:
            d["all_codes"].append(codes[i])
            if 9 <= int(t[11:13]) <= 18:      # symbol dňa berieme z denných hodín
                d["day_codes"].append(codes[i])

    day_list = []
    for d in list(days.values())[:FORECAST_DAYS]:
        # neúplný chvost horizontu modelu (napr. ICON končí o polnoci
        # posledného dňa) by dal skreslené min/max — deň vynecháme
        if len(d["temps"]) < 18:
            continue
        pool = d["day_codes"] or d["all_codes"]
        day_list.append({
            "date": d["date"],
            "temp_min": round(min(d["temps"]), 1),
            "temp_max": round(max(d["temps"]), 1),
            "precip": round(d["precip"], 1),
            "wind_max": round(max(d["winds"]), 1) if d["winds"] else None,
            "wmo": Counter(pool).most_common(1)[0][0] if pool else None,
        })

    return day_list
