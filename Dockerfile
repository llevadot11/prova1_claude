FROM python:3.11-slim

WORKDIR /app

# Crear directorios de datos para que la app no falle en cold start sin parquet
RUN mkdir -p /data/processed /data/cache /data/raw

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY backend/app ./app

EXPOSE 8000

# Railway sobreescribe CMD con startCommand de railway.json
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
