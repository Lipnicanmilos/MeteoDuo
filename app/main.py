"""MeteoDuo — dve predpovede vedľa seba (yr.no / MET Norway + SHMÚ ALADIN)."""
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response

from app.services import geocode, shmu, yr

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(follow_redirects=True)
    yield
    await app.state.http.aclose()


app = FastAPI(title="MeteoDuo", lifespan=lifespan)


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/cities")
async def cities():
    return shmu.CITIES


@app.get("/api/forecast/{city_id}")
async def forecast(city_id: str):
    if city_id not in shmu.CITY_IDS:
        raise HTTPException(404, "Neznáme mesto")

    client = app.state.http
    name = shmu.CITY_NAMES[city_id]

    coords = await geocode.geocode(client, name)
    yr_data, yr_error = None, None
    if coords:
        try:
            yr_data = await yr.fetch_forecast(client, *coords)
        except httpx.HTTPError as e:
            yr_error = f"MET Norway API nedostupné ({e.__class__.__name__})"
    else:
        yr_error = "Miesto sa nepodarilo geokódovať"

    return {
        "city": {"id": city_id, "name": name,
                 "lat": coords[0] if coords else None,
                 "lon": coords[1] if coords else None},
        "yr": yr_data,
        "yr_error": yr_error,
        "meteogram_url": f"/api/meteogram/{city_id}",
    }


@app.get("/api/meteogram/{city_id}")
async def meteogram(city_id: str):
    if city_id not in shmu.CITY_IDS:
        raise HTTPException(404, "Neznáme mesto")
    try:
        png = await shmu.fetch_meteogram_png(app.state.http, city_id)
    except httpx.HTTPError:
        raise HTTPException(502, "SHMÚ nedostupné")
    if png is None:
        raise HTTPException(404, "Meteogram sa nenašiel")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=600"})


@app.get("/health")
async def health():
    return {"status": "ok"}
