FROM python:3.12-slim

WORKDIR /app

# DejaVu font — Pillow ho potrebuje na text tapety (/wallpaper.png), vrátane
# slovenskej diakritiky; python-slim žiadny TTF neobsahuje
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY static/ static/

# JSX predkompilované už pri builde — cold start preskočí pomalú kompiláciu
# cez dukpy/Babel (v /app.js beží aj in-memory fallback, ak by FS bol read-only)
RUN python -c "import pathlib, dukpy; p = pathlib.Path('static'); (p / 'app.compiled.js').write_text(dukpy.jsx_compile((p / 'app.jsx').read_text(encoding='utf-8')), encoding='utf-8')"

# Render (aj iné PaaS) posiela port cez $PORT; lokálne default 8080.
# Shell forma CMD, aby sa ${PORT} rozvinul.
EXPOSE 8080
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips "*"
