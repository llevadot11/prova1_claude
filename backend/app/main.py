import json
import logging
import logging.config
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse

from app import cache as cache_module
from app import enrichment, explain as explain_module
from app import health, store
from app.config import settings
from app.modes import MODES
from app.schemas import (
    ExplainResponse,
    HealthStatus,
    Mode,
    ModePreset,
    TramosStateResponse,
    UFIResponse,
)

# ---------------------------------------------------------------------------
# Logging estructurado UTC
# ---------------------------------------------------------------------------

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "utc": {
            "format": "%(asctime)s UTC %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "utc"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
})
logging.Formatter.converter = __import__("time").gmtime  # force UTC

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — validación de schema al arrancar (P6)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ufi_parquet.exists():
        missing = store.validate_parquet_schema()
        if missing:
            logger.warning("Parquet missing columns %s — UFI will use stubs", missing)
        else:
            logger.info("Parquet schema validated OK (%s)", settings.ufi_parquet)
    else:
        logger.info("Parquet not found at %s — UFI running on deterministic stubs", settings.ufi_parquet)
    yield


# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------

app = FastAPI(title="UFI Barcelona API", version="0.1.0", lifespan=lifespan)

_origins = (
    ["*"] if settings.cors_origins == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_at(at: str | None) -> datetime:
    if at is None:
        return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    try:
        dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(400, f"Invalid `at` (ISO 8601 expected): {e}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/barrios")
def get_barrios() -> dict:
    return store.load_barrios_geojson()


@app.get("/tramos")
def get_tramos() -> dict:
    return store.load_tramos_geojson()


@app.get("/ufi", response_model=UFIResponse)
def get_ufi(
    at: str | None = Query(default=None, description="ISO 8601, default = ahora UTC redondeada"),
    mode: Mode = "default",
) -> UFIResponse:
    when = _parse_at(at)
    return UFIResponse(at=when, mode=mode, barrios=store.load_ufi(when, mode))


@app.get("/tramos/state", response_model=TramosStateResponse)
def get_tramos_state(at: str | None = Query(default=None)) -> TramosStateResponse:
    when = _parse_at(at)
    return TramosStateResponse(at=when, tramos=store.load_tramos_state(when))


@app.get("/barrio/{barrio_id}")
async def get_barrio(
    barrio_id: str,
    at: str | None = Query(default=None),
    mode: Mode = "default",
):
    when = _parse_at(at)
    detail = store.load_barrio_detail(barrio_id, when, mode)
    if detail is None:
        raise HTTPException(404, f"barrio_id `{barrio_id}` no encontrado")
    enriched = await enrichment.get_enriched_raw(barrio_id, when)
    if enriched:
        detail = detail.model_copy(update={"raw": {**detail.raw, **enriched}})
    return detail


@app.get("/explain/{barrio_id}", response_model=ExplainResponse)
async def get_explain(
    barrio_id: str,
    at: str | None = Query(default=None),
    mode: Mode = "default",
) -> ExplainResponse:
    when = _parse_at(at)
    detail = store.load_barrio_detail(barrio_id, when, mode)
    if detail is None:
        raise HTTPException(404, f"barrio_id `{barrio_id}` no encontrado")
    enriched = await enrichment.get_enriched_raw(barrio_id, when)
    if enriched:
        detail = detail.model_copy(update={"raw": {**detail.raw, **enriched}})
    return await explain_module.explain(detail)


@app.get("/explain/{barrio_id}/stream")
async def get_explain_stream(
    barrio_id: str,
    at: str | None = Query(default=None),
    mode: Mode = "default",
) -> StreamingResponse:
    """SSE stream of the explanation text. Each event: data: {"text":"...", "done": bool}"""
    when = _parse_at(at)
    detail = store.load_barrio_detail(barrio_id, when, mode)
    if detail is None:
        raise HTTPException(404, f"barrio_id `{barrio_id}` no encontrado")
    enriched = await enrichment.get_enriched_raw(barrio_id, when)
    if enriched:
        detail = detail.model_copy(update={"raw": {**detail.raw, **enriched}})

    # Serve from cache immediately if available
    cache_key = f"explain:{explain_module._signature(detail)}"
    cached_text = cache_module.get(cache_key)
    if cached_text:
        async def _cached() -> AsyncIterator[str]:
            yield f"data: {json.dumps({'text': cached_text, 'cached': True, 'done': True})}\n\n"
        return StreamingResponse(_cached(), media_type="text/event-stream")

    async def _live() -> AsyncIterator[str]:
        async for chunk in explain_module.explain_stream(detail):
            yield f"data: {json.dumps({'text': chunk, 'cached': False, 'done': False})}\n\n"
        yield f"data: {json.dumps({'text': '', 'cached': False, 'done': True})}\n\n"

    return StreamingResponse(_live(), media_type="text/event-stream")


@app.get("/modes", response_model=list[ModePreset])
def get_modes() -> list[ModePreset]:
    return list(MODES.values())


@app.get("/health", response_model=HealthStatus)
async def get_health() -> HealthStatus:
    return await health.collect()


# ---------------------------------------------------------------------------
# Snapshot (P5) — generado por D antes de la demo, servido en /snapshot
# ---------------------------------------------------------------------------

@app.get("/snapshot")
def get_snapshot():
    """Sirve el snapshot pre-generado de /ufi. Si no existe, devuelve /ufi en vivo."""
    if settings.snapshot_json.exists():
        return json.loads(settings.snapshot_json.read_text(encoding="utf-8"))
    when = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return UFIResponse(at=when, mode="default", barrios=store.load_ufi(when, "default"))


@app.post("/snapshot/generate", status_code=201)
def generate_snapshot():
    """Genera y guarda snapshot de /ufi para todos los modos. Ejecutar antes de la demo."""
    when = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    payload: dict = {"generated_at": when.isoformat(), "modes": {}}
    for mode in ("default", "familiar", "runner", "movilidad_reducida"):
        resp = UFIResponse(at=when, mode=mode, barrios=store.load_ufi(when, mode))  # type: ignore[arg-type]
        payload["modes"][mode] = resp.model_dump(mode="json")
    settings.snapshot_json.parent.mkdir(parents=True, exist_ok=True)
    settings.snapshot_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Snapshot generated at %s (%d modes)", settings.snapshot_json, len(payload["modes"]))
    return {"generated_at": when.isoformat(), "modes": list(payload["modes"].keys())}
