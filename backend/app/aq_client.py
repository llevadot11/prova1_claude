"""Wrapper async para Open-Meteo Air Quality API con cache SQLite 30 min."""
from __future__ import annotations

import json
from datetime import date, datetime

import httpx

from app import cache as cache_module
from app.config import settings

_TTL = 30 * 60  # 30 minutos

_HOURLY_VARS = "pm10,pm2_5,nitrogen_dioxide,ozone"


def _cache_key(lat: float, lon: float, day: date) -> str:
    return f"aq:{lat:.4f}:{lon:.4f}:{day.isoformat()}"


async def get_air_quality(lat: float, lon: float, dt: datetime) -> dict:
    """Devuelve variables de calidad del aire para (lat, lon) en la hora de dt.

    Retorna dict plano:
        pm10, pm2_5, nitrogen_dioxide, ozone  (µg/m³, floats o None)
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
        r = await cli.get(settings.open_meteo_aq_url, params=params)
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

    def _val(key: str) -> float | None:
        vals = hourly.get(key, [])
        if idx is None or idx >= len(vals):
            return None
        v = vals[idx]
        return float(v) if v is not None else None

    return {
        "pm10": _val("pm10"),
        "pm2_5": _val("pm2_5"),
        "nitrogen_dioxide": _val("nitrogen_dioxide"),
        "ozone": _val("ozone"),
    }


def aq_offline() -> dict:
    """Fallback sin red: valores neutros para modo demo."""
    return {
        "pm10": 15.0,
        "pm2_5": 8.0,
        "nitrogen_dioxide": 25.0,
        "ozone": 80.0,
    }
