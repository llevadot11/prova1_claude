FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /data/processed /data/cache /data/raw

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY backend/app ./app

# Datos esenciales para el backend (GeoJSONs + Parquet UFI).
# Se generan con: cd data-ml && python -m ml.score
# y se committean al repo para que Railway los incluya en la imagen.
COPY data/processed/barrios.geojson      /data/processed/barrios.geojson
COPY data/processed/tramos.geojson       /data/processed/tramos.geojson
COPY data/processed/mapping_barrios.csv  /data/processed/mapping_barrios.csv
COPY data/processed/ufi_latest.parquet   /data/processed/ufi_latest.parquet

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
