"""Descarga Open-Meteo Forecast + AQ para los 73 centroides de barrio.

Outputs:
  data/processed/meteo_73pts.parquet   (barrio_id, time, temperature_2m, precipitation, wind_speed_10m)
  data/processed/aire_73pts.parquet    (barrio_id, time, pm10, nitrogen_dioxide, ozone)
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

from data.paths import PROCESSED, BARRIOS_GEOJSON

log = logging.getLogger(__name__)

METEO_URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

METEO_73_PARQUET = PROCESSED / "meteo_73pts.parquet"
AIRE_73_PARQUET = PROCESSED / "aire_73pts.parquet"


def _get_centroids() -> pd.DataFrame:
    """Calcula centroides WGS84 de los 73 barrios."""
    barrios = gpd.read_file(BARRIOS_GEOJSON)
    barrios = barrios.set_crs(epsg=4326)
    # Proyectar a UTM para centroide preciso, luego volver a WGS84
    barrios_utm = barrios.to_crs(epsg=25831)
    barrios["centroid"] = barrios_utm.geometry.centroid.to_crs(epsg=4326)
    centroids = pd.DataFrame({
        "barrio_id": barrios["barrio_id"],
        "lat": barrios["centroid"].y,
        "lon": barrios["centroid"].x,
    })
    return centroids


def _fetch_meteo(lat: float, lon: float, barrio_id: str) -> pd.DataFrame | None:
    params = {
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "hourly": "temperature_2m,precipitation,wind_speed_10m",
        "forecast_days": 3,
        "timezone": "UTC",
    }
    try:
        r = requests.get(METEO_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["hourly"]
        df = pd.DataFrame({
            "barrio_id": barrio_id,
            "time": pd.to_datetime(data["time"]),
            "temperature_2m": data["temperature_2m"],
            "precipitation": data["precipitation"],
            "wind_speed_10m": data["wind_speed_10m"],
        })
        return df
    except Exception as e:
        log.warning("Error meteo %s: %s", barrio_id, e)
        return None


def _fetch_aire(lat: float, lon: float, barrio_id: str) -> pd.DataFrame | None:
    params = {
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "hourly": "pm10,nitrogen_dioxide,ozone",
        "forecast_days": 3,
        "timezone": "UTC",
    }
    try:
        r = requests.get(AQ_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["hourly"]
        df = pd.DataFrame({
            "barrio_id": barrio_id,
            "time": pd.to_datetime(data["time"]),
            "pm10": data["pm10"],
            "nitrogen_dioxide": data["nitrogen_dioxide"],
            "ozone": data["ozone"],
        })
        return df
    except Exception as e:
        log.warning("Error aire %s: %s", barrio_id, e)
        return None


def ingest_meteo_73pts() -> pd.DataFrame:
    centroids = _get_centroids()
    frames = []
    for _, row in centroids.iterrows():
        df = _fetch_meteo(row["lat"], row["lon"], row["barrio_id"])
        if df is not None:
            frames.append(df)
        time.sleep(0.05)  # respetar rate limit Open-Meteo

    result = pd.concat(frames, ignore_index=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    result.to_parquet(METEO_73_PARQUET, index=False)
    log.info("meteo_73pts.parquet: %d filas, %d barrios", len(result), result["barrio_id"].nunique())
    return result


def ingest_aire_73pts() -> pd.DataFrame:
    centroids = _get_centroids()
    frames = []
    for _, row in centroids.iterrows():
        df = _fetch_aire(row["lat"], row["lon"], row["barrio_id"])
        if df is not None:
            frames.append(df)
        time.sleep(0.05)

    result = pd.concat(frames, ignore_index=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    result.to_parquet(AIRE_73_PARQUET, index=False)
    log.info("aire_73pts.parquet: %d filas, %d barrios", len(result), result["barrio_id"].nunique())
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log.info("Descargando meteo para 73 barrios...")
    ingest_meteo_73pts()
    log.info("Descargando AQ para 73 barrios...")
    ingest_aire_73pts()
    print("Meteo+AQ 73pts OK")


if __name__ == "__main__":
    main()
