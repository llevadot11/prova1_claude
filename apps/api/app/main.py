from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import explain as explain_module
from app import health, store
from app.modes import MODES
from app.schemas import (
    ExplainResponse,
    HealthStatus,
    Mode,
    ModePreset,
    TramosStateResponse,
    UFIResponse,
)

app = FastAPI(title="UFI Barcelona API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


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
def get_barrio(
    barrio_id: str,
    at: str | None = Query(default=None),
    mode: Mode = "default",
):
    when = _parse_at(at)
    detail = store.load_barrio_detail(barrio_id, when, mode)
    if detail is None:
        raise HTTPException(404, f"barrio_id `{barrio_id}` no encontrado")
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
    return await explain_module.explain(detail)


@app.get("/modes", response_model=list[ModePreset])
def get_modes() -> list[ModePreset]:
    return list(MODES.values())


@app.get("/health", response_model=HealthStatus)
async def get_health() -> HealthStatus:
    return await health.collect()
