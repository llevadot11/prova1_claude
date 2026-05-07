"""Wrapper async para Open-Meteo Forecast API con cache SQLite 30 min."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import httpx

from app import cache as cache_module
from app.config import settings

_TTL = 30 * 60  # 30 minutos

# Variables que pedimos a Open-Meteo por hora
_HOURLY_VARS = "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m,weather_code"


def _cache_key(lat: float, lon: float, day: date) -> str:
    return f"meteo:{lat:.4f}:{lon:.4f}:{day.isoformat()}"


async def get_forecast(lat: float, lon: float, dt: datetime) -> dict:
    """Devuelve variables horarias de Open-Meteo para (lat, lon) en la hora de dt.

    Retorna un dict plano con las claves:
        temperature_2m, precipitation, wind_speed_10m,
        relative_humidity_2m, weather_code
    todos floats/ints, o None si no disponible.
    """
    day = dt.date()
    key = _cache_key(lat, lon, day)

    cached = cache_module.get(key)
    if cached is not None:
        daily_data: dict = json.loads(cached)
    else:
        daily_data = await _fetch(lat, lon, day)
        cache_module.put(key, json.dumps(daily_data), _TTL)

    return _extract_hour(daily_data, dt)


async def _fetch(lat: float, lon: float, day: date) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": _HOURLY_VARS,
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
        "timezone": "UTC",
    }
    async with httpx.AsyncClient(timeout=8.0) as cli:
        r = await cli.get(settings.open_meteo_forecast_url, params=params)
        r.raise_for_status()
        return r.json()


def _extract_hour(data: dict, dt: datetime) -> dict:
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    target = dt.replace(minute=0, second=0, microsecond=0, tzinfo=None).isoformat()

    idx: int | None = None
    for i, t in enumerate(times):
        if t == target:
            idx = i
            break

    def _val(key: str) -> float | int | None:
        vals = hourly.get(key, [])
        if idx is None or idx >= len(vals):
            return None
        return vals[idx]

    return {
        "temperature_2m": _val("temperature_2m"),
        "precipitation": _val("precipitation"),
        "wind_speed_10m": _val("wind_speed_10m"),
        "relative_humidity_2m": _val("relative_humidity_2m"),
        "weather_code": _val("weather_code"),
    }


async def get_forecast_for_barrio(barrio_centroid: tuple[float, float], dt: datetime) -> dict:
    """Conveniencia: acepta (lat, lon) como tupla."""
    lat, lon = barrio_centroid
    return await get_forecast(lat, lon, dt)


def forecast_offline() -> dict:
    """Fallback sin red: valores neutros para modo demo."""
    return {
        "temperature_2m": 18.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "relative_humidity_2m": 60.0,
        "weather_code": 0,
    }
