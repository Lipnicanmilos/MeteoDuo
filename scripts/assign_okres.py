"""Jednorazový skript: doplní `okres` do app/data/cities.json.

Okres potrebujeme na priradenie výstrah Meteoalarm/SHMÚ (tie sú na úrovni
okresu). Open-Meteo geocoding vracia `admin2` = 'Okres Námestovo'; obec už
má presné súradnice, tak z výsledkov vyberieme ten najbližší (nie len podľa
mena — vyhne sa to zámene rovnomenných obcí).

Spustenie:  .venv\\Scripts\\python scripts\\assign_okres.py
"""
import asyncio
import json
import re
import sys
from pathlib import Path

import httpx

CITIES_FILE = Path(__file__).resolve().parent.parent / "app" / "data" / "cities.json"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
CONCURRENCY = 8
MAX_DEG = 0.25   # ~25 km: výsledok ďalej než toto neberieme (zlá zhoda)


def _clean_name(name: str) -> str:
    name = re.sub(r"\(.*?\)", "", name)
    name = name.split(" - ")[0]
    return name.strip()


def _strip_okres(admin2: str | None) -> str | None:
    if not admin2:
        return None
    s = admin2.strip()
    return s[6:].strip() if s.lower().startswith("okres ") else s


async def assign_one(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                     city: dict) -> None:
    if city.get("lat") is None:
        return
    async with sem:
        for attempt in (1, 2):
            try:
                res = await client.get(
                    GEOCODE_URL,
                    params={"name": _clean_name(city["name"]), "count": 100,
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

    best, best_d = None, MAX_DEG ** 2
    for r in results:
        if r.get("country_code") != "SK" or not r.get("admin2"):
            continue
        d = (r["latitude"] - city["lat"]) ** 2 + (r["longitude"] - city["lon"]) ** 2
        if d < best_d:
            best, best_d = r, d
    if best:
        city["okres"] = _strip_okres(best["admin2"])


async def main() -> None:
    cities = json.loads(CITIES_FILE.read_text(encoding="utf-8"))
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [assign_one(client, sem, c) for c in cities]
        for chunk in range(0, len(tasks), 100):
            await asyncio.gather(*tasks[chunk:chunk + 100])
            print(f"{min(chunk + 100, len(tasks))}/{len(tasks)}", flush=True)

    missing = [c["name"] for c in cities if not c.get("okres")]
    CITIES_FILE.write_text(
        json.dumps(cities, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"Hotovo: {len(cities) - len(missing)}/{len(cities)} s okresom")
    if missing:
        print(f"Bez okresu ({len(missing)}): {', '.join(missing[:20])}"
              + (" …" if len(missing) > 20 else ""))


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
