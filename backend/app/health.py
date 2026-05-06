from __future__ import annotations

import asyncio
from typing import Literal

import httpx

from app import store
from app.config import settings
from app.schemas import HealthStatus

Status = Literal["ok", "degraded", "down", "unknown"]


async def _ping(url: str) -> Status:
    if settings.demo_offline:
        return "unknown"
    try:
        async with httpx.AsyncClient(timeout=3.0) as cli:
            r = await cli.head(url)
            return "ok" if r.status_code < 500 else "degraded"
    except Exception:
        return "down"


async def collect() -> HealthStatus:
    om, oma = await asyncio.gather(
        _ping(settings.open_meteo_forecast_url),
        _ping(settings.open_meteo_aq_url),
    )
    anthropic_status: Status = "ok" if settings.anthropic_api_key else "unknown"
    return HealthStatus(
        api="ok",
        open_meteo=om,
        open_meteo_aq=oma,
        anthropic=anthropic_status,
        demo_offline=settings.demo_offline,
        ufi_parquet_age_seconds=store.ufi_parquet_age(),
    )
