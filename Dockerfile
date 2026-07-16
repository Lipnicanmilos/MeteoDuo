FROM python:3.12-slim

# Lambda Web Adapter — v AWS Lambda prekladá udalosti na HTTP pre uvicorn,
# mimo Lambdy sa neaktivuje (image beží normálne aj lokálne / v inom hostingu)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY static/ static/

# JSX predkompilované už pri builde — runtime filesystem môže byť read-only
# (AWS Lambda) a cold start preskočí pomalú kompiláciu cez dukpy/Babel
RUN python -c "import pathlib, dukpy; p = pathlib.Path('static'); (p / 'app.compiled.js').write_text(dukpy.jsx_compile((p / 'app.jsx').read_text(encoding='utf-8')), encoding='utf-8')"

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
