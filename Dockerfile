FROM python:3.12-slim

# Lambda Web Adapter — v AWS Lambda prekladá udalosti na HTTP pre uvicorn,
# mimo Lambdy sa neaktivuje (image beží normálne aj lokálne / v inom hostingu)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY static/ static/

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
