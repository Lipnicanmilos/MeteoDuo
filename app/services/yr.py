"""Predpoveď z MET Norway (dáta, ktoré zobrazuje yr.no).

Locationforecast 2.0: https://api.met.no/weatherapi/locationforecast/2.0/documentation
Podmienky použitia vyžadujú identifikujúci User-Agent a uvedenie zdroja
(CC BY 4.0, MET Norway).
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx

MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
USER_AGENT = "MeteoDuo/1.0 https://github.com/Lipnicanmilos/meteoduo"

# cache: (lat, lon) -> (expires_utc, payload)
_cache: dict[tuple[float, float], tuple[datetime, dict]] = {}
CACHE_TTL = timedelta(minutes=15)
# MET Norway dáva ~9-10 dní (po ~60 h už len 6-hodinové kroky)
FORECAST_DAYS = 10


async def fetch_forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Vráti {'hourly': [...], 'days': [...]} na najbližších FORECAST_DAYS dní."""
    key = (round(lat, 3), round(lon, 3))
    now = datetime.now(timezone.utc)
    cached = _cache.get(key)
    if cached and cached[0] > now:
        return cached[1]

    res = await client.get(
        MET_URL,
        params={"lat": key[0], "lon": key[1]},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    res.raise_for_status()
    timeseries = res.json()["properties"]["timeseries"]

    payload = _digest(timeseries)
    _cache[key] = (now + CACHE_TTL, payload)
    return payload


def _digest(timeseries: list[dict]) -> dict:
    horizon = datetime.now(timezone.utc) + timedelta(days=FORECAST_DAYS)
    hourly = []
    for entry in timeseries:
        t = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        if t > horizon:
            break
        details = entry["data"]["instant"]["details"]
        next1 = entry["data"].get("next_1_hours") or entry["data"].get("next_6_hours")
        hourly.append({
            "time": entry["time"],
            "temp": details.get("air_temperature"),
            "wind": details.get("wind_speed"),
            "wind_dir": details.get("wind_from_direction"),
            "humidity": details.get("relative_humidity"),
            "pressure": details.get("air_pressure_at_sea_level"),
            "precip": (next1 or {}).get("details", {}).get("precipitation_amount"),
            "symbol": (next1 or {}).get("summary", {}).get("symbol_code"),
        })

    days: dict[str, dict] = {}
    for h in hourly:
        day = h["time"][:10]
        d = days.setdefault(day, {"date": day, "temps": [], "precip": 0.0,
                                  "winds": [], "symbols": []})
        if h["temp"] is not None:
            d["temps"].append(h["temp"])
        if h["precip"] is not None:
            d["precip"] += h["precip"]
        if h["wind"] is not None:
            d["winds"].append(h["wind"])
        # symbol reprezentujúci deň berieme z denných hodín
        hour = int(h["time"][11:13])
        if h["symbol"] and 9 <= hour <= 18:
            d["symbols"].append(h["symbol"])

    # posledný deň horizontu býva odrezaný uprostred dňa -> skreslené max;
    # nechávame ho, len ak dáta siahajú aspoň po 18:00 (po 60 h sú kroky 6 h)
    last_day = max(days) if days else None
    if last_day and not any(h["time"][:10] == last_day and h["time"][11:13] >= "18"
                            for h in hourly):
        del days[last_day]

    day_list = []
    for d in list(days.values())[:FORECAST_DAYS]:
        if not d["temps"]:
            continue
        symbols = d["symbols"] or [h["symbol"] for h in hourly if h["time"][:10] == d["date"] and h["symbol"]]
        day_list.append({
            "date": d["date"],
            "temp_min": round(min(d["temps"]), 1),
            "temp_max": round(max(d["temps"]), 1),
            "precip": round(d["precip"], 1),
            "wind_max": round(max(d["winds"]), 1) if d["winds"] else None,
            "symbol": Counter(symbols).most_common(1)[0][0] if symbols else None,
        })

    return {"hourly": hourly, "days": day_list}
