"""Enriquecimiento de raw values con datos reales de Open-Meteo (P2).

Extrae el centroide del barrio del GeoJSON de C si está disponible,
y llama a meteo_client + aq_client en paralelo.
Devuelve {} en cualquier error — nunca rompe el endpoint.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from app import aq_client, meteo_client
from app.config import settings

logger = logging.getLogger(__name__)

# Centroide por defecto: centro de Barcelona
_BCN_CENTER: tuple[float, float] = (41.3888, 2.1590)

# Cache en memoria de centroides extraídos del GeoJSON (se carga una vez)
_centroids_cache: dict[str, tuple[float, float]] | None = None


def _load_centroids() -> dict[str, tuple[float, float]]:
    global _centroids_cache
    if _centroids_cache is not None:
        return _centroids_cache

    if not settings.barrios_geojson.exists():
        _centroids_cache = {}
        return _centroids_cache

    try:
        geojson = json.loads(settings.barrios_geojson.read_text(encoding="utf-8"))
        result: dict[str, tuple[float, float]] = {}
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            bid = props.get("barrio_id")
            if not bid:
                continue
            geom = feature.get("geometry")
            if not geom:
                continue
            if geom["type"] == "Polygon":
                coords = geom["coordinates"][0]
                lat = sum(c[1] for c in coords) / len(coords)
                lon = sum(c[0] for c in coords) / len(coords)
                result[bid] = (lat, lon)
            elif geom["type"] == "MultiPolygon":
                all_coords = [c for poly in geom["coordinates"] for c in poly[0]]
                lat = sum(c[1] for c in all_coords) / len(all_coords)
                lon = sum(c[0] for c in all_coords) / len(all_coords)
                result[bid] = (lat, lon)
        _centroids_cache = result
        logger.info("Loaded %d barrio centroids from GeoJSON", len(result))
    except Exception as exc:
        logger.warning("Could not load centroids from GeoJSON: %s", exc)
        _centroids_cache = {}

    return _centroids_cache


def get_centroid(barrio_id: str) -> tuple[float, float]:
    """Returns (lat, lon) centroid for barrio_id, or Barcelona center as fallback."""
    return _load_centroids().get(barrio_id, _BCN_CENTER)


def invalidate_centroids_cache() -> None:
    """Call this if barrios.geojson is replaced at runtime."""
    global _centroids_cache
    _centroids_cache = None


async def get_enriched_raw(barrio_id: str, at: datetime) -> dict:
    """Returns real meteo + AQ values for a barrio at a given time.

    Returns {} silently on any error so callers always get a valid (possibly empty) dict.
    """
    if settings.demo_offline:
        return {}

    lat, lon = get_centroid(barrio_id)

    try:
        meteo, aq = await asyncio.gather(
            meteo_client.get_forecast(lat, lon, at),
            aq_client.get_air_quality(lat, lon, at),
        )
    except Exception as exc:
        logger.warning("Enrichment failed for %s: %s", barrio_id, exc)
        return {}

    return {
        "temperature_2m": meteo.get("temperature_2m"),
        "precipitation_mm": meteo.get("precipitation"),
        "wind_speed_10m": meteo.get("wind_speed_10m"),
        "relative_humidity_2m": meteo.get("relative_humidity_2m"),
        "pm2_5": aq.get("pm2_5"),
        "no2": aq.get("nitrogen_dioxide"),
        "pm10": aq.get("pm10"),
        "ozone": aq.get("ozone"),
    }
