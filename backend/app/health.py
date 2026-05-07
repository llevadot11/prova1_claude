from __future__ import annotations

import asyncio
import logging
import time
from typing import Literal

import httpx

from app import store
from app.config import settings
from app.schemas import HealthStatus

logger = logging.getLogger(__name__)

Status = Literal["ok", "degraded", "down", "unknown"]

_ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models"


async def _ping(url: str, name: str) -> Status:
    if settings.demo_offline:
        return "unknown"
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=3.0) as cli:
            r = await cli.head(url)
        latency_ms = (time.monotonic() - t0) * 1000
        status: Status = "ok" if r.status_code < 500 else "degraded"
        logger.info("health ping %s → %s (%.0f ms)", name, status, latency_ms)
        return status
    except Exception as exc:
        latency_ms = (time.monotonic() - t0) * 1000
        logger.warning("health ping %s → down after %.0f ms: %s", name, latency_ms, exc)
        return "down"


async def _ping_anthropic() -> Status:
    if not settings.anthropic_api_key:
        return "unknown"
    if settings.demo_offline:
        return "unknown"
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=3.0) as cli:
            r = await cli.get(
                _ANTHROPIC_MODELS_URL,
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
        latency_ms = (time.monotonic() - t0) * 1000
        # 200 = ok, 401 = bad key (key present but invalid), ≥500 = degraded
        if r.status_code == 200:
            status: Status = "ok"
        elif r.status_code < 500:
            status = "degraded"
        else:
            status = "down"
        logger.info("health ping anthropic → %s (%.0f ms)", status, latency_ms)
        return status
    except Exception as exc:
        latency_ms = (time.monotonic() - t0) * 1000
        logger.warning("health ping anthropic → down after %.0f ms: %s", latency_ms, exc)
        return "down"


async def collect() -> HealthStatus:
    om, oma, anthropic = await asyncio.gather(
        _ping(settings.open_meteo_forecast_url, "open_meteo"),
        _ping(settings.open_meteo_aq_url, "open_meteo_aq"),
        _ping_anthropic(),
    )
    return HealthStatus(
        api="ok",
        open_meteo=om,
        open_meteo_aq=oma,
        anthropic=anthropic,
        demo_offline=settings.demo_offline,
        ufi_parquet_age_seconds=store.ufi_parquet_age(),
    )
