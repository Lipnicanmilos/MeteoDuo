"""Jednorazový skript: doplní lat/lon do app/data/cities.json.

Geokóduje cez Open-Meteo Geocoding API (rovnaká logika ako app/services/
geocode.py). Obce, ktoré sa nepodarí geokódovať, ostanú bez súradníc —
runtime pre ne použije geocode.py ako fallback.

Spustenie:  .venv\\Scripts\\python scripts\\geocode_cities.py
"""
import asyncio
import json
import re
import sys
import unicodedata
from pathlib import Path

import httpx

CITIES_FILE = Path(__file__).resolve().parent.parent / "app" / "data" / "cities.json"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = "MeteoDuo one-off geocode script (github.com/Lipnicanmilos/MeteoDuo)"
CONCURRENCY = 8


def _clean_name(name: str) -> str:
    name = re.sub(r"\(.*?\)", "", name)
    name = name.split(" - ")[0]
    return name.strip()


def _norm(s: str) -> str:
    """Bez diakritiky, lowercase — na porovnanie SHMÚ názvov s API názvami."""
    return (unicodedata.normalize("NFD", s)
            .encode("ascii", "ignore").decode().lower())


async def geocode_fuzzy(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                        city: dict) -> None:
    """Tretie kolo: hľadá len prvé slovo, výsledok musí sedieť celým
    normalizovaným názvom (SHMÚ názvy sú bez diakritiky, viacslovné
    dopyty API často nenájde)."""
    if city.get("lat") is not None:
        return
    cleaned = _clean_name(city["name"])
    target = _norm(cleaned)
    query = re.split(r"[ -]", cleaned)[0]
    if len(query) < 3:
        return
    async with sem:
        try:
            res = await client.get(
                GEOCODE_URL,
                params={"name": query, "count": 100, "language": "sk"},
                timeout=15,
            )
            res.raise_for_status()
            results = res.json().get("results") or []
        except httpx.HTTPError:
            return
    for r in results:
        if r.get("country_code") == "SK" and _norm(r["name"]) == target:
            city["lat"] = round(r["latitude"], 5)
            city["lon"] = round(r["longitude"], 5)
            return


async def geocode_one(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                      city: dict, count: int = 10) -> None:
    if city.get("lat") is not None:
        return
    async with sem:
        for attempt in (1, 2):
            try:
                res = await client.get(
                    GEOCODE_URL,
                    params={"name": _clean_name(city["name"]), "count": count,
                            "language": "sk"},
                    timeout=15,
                )
                res.raise_for_status()
                results = res.json().get("results") or []
                break
            except httpx.HTTPError:
                if attempt == 2:
                    return
                await asyncio.sleep(2)

    for r in results:
        if r.get("country_code") == "SK":
            city["lat"] = round(r["latitude"], 5)
            city["lon"] = round(r["longitude"], 5)
            return


async def main() -> None:
    cities = json.loads(CITIES_FILE.read_text(encoding="utf-8"))
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [geocode_one(client, sem, c) for c in cities]
        done = 0
        for chunk in range(0, len(tasks), 100):
            await asyncio.gather(*tasks[chunk:chunk + 100])
            done = min(chunk + 100, len(tasks))
            print(f"{done}/{len(tasks)}", flush=True)

    # druhé kolo pre nenájdené: širší zoznam výsledkov (SHMÚ názvy sú bez
    # diakritiky, SK obec býva hlbšie v poradí)
    retry = [c for c in cities if c.get("lat") is None]
    if retry:
        print(f"Druhé kolo (count=100) pre {len(retry)} obcí…", flush=True)
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[geocode_one(client, sem, c, count=100)
                                   for c in retry])

    retry2 = [c for c in cities if c.get("lat") is None]
    if retry2:
        print(f"Tretie kolo (prvé slovo + presná zhoda) pre {len(retry2)} obcí…",
              flush=True)
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[geocode_fuzzy(client, sem, c)
                                   for c in retry2])

    # štvrté kolo: Nominatim (OSM) — pozná aj malé obce a chaty, ktoré
    # Open-Meteo geokóder nemá; sekvenčne max ~1 req/s podľa usage policy
    retry3 = [c for c in cities if c.get("lat") is None]
    if retry3:
        print(f"Štvrté kolo (Nominatim) pre {len(retry3)} obcí…", flush=True)
        async with httpx.AsyncClient(
                headers={"User-Agent": NOMINATIM_UA}) as client:
            for c in retry3:
                try:
                    res = await client.get(
                        NOMINATIM_URL,
                        params={"q": _clean_name(c["name"]),
                                "countrycodes": "sk",
                                "format": "jsonv2", "limit": 1},
                        timeout=15,
                    )
                    res.raise_for_status()
                    hits = res.json()
                    if hits:
                        c["lat"] = round(float(hits[0]["lat"]), 5)
                        c["lon"] = round(float(hits[0]["lon"]), 5)
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1.1)

    missing = [c["name"] for c in cities if c.get("lat") is None]
    CITIES_FILE.write_text(
        json.dumps(cities, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"Hotovo: {len(cities) - len(missing)}/{len(cities)} geokódovaných")
    if missing:
        print(f"Bez súradníc ({len(missing)}): {', '.join(missing[:20])}"
              + (" …" if len(missing) > 20 else ""))


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
