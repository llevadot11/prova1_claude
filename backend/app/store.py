"""Lectura de Parquet/GeoJSON en disco. Stub determinista si no hay ficheros aún.

Schema del Parquet (contrato con Persona C — NO romper sin avisar):
    barrio_id: str
    timestamp: datetime (UTC, hora redondeada)
    ufi_default: float  (0–100)
    score_trafico: float       (0–1)
    score_accidentes: float    (0–1)
    score_aire: float          (0–1)
    score_meteo: float         (0–1)
    score_sensibilidad: float  (0–1)
"""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from app.config import settings
from app.modes import MODES
from app.schemas import (
    BarrioDetail,
    BarrioUFI,
    FamilyContribution,
    Mode,
    TramoState,
)

logger = logging.getLogger(__name__)

# 73 barrios placeholder hasta que C suba el GeoJSON
DUMMY_BARRIOS = [f"BAR-{i:03d}" for i in range(1, 74)]

_FAMILIES = ("trafico", "accidentes", "aire", "meteo", "sensibilidad")

_REQUIRED_PARQUET_COLS = {
    "barrio_id", "timestamp",
    "score_trafico", "score_accidentes", "score_aire",
    "score_meteo", "score_sensibilidad",
}

# In-memory TTL cache for load_ufi (P4) — avoids re-reading DuckDB on every request
_ufi_cache: dict[str, tuple[float, list[BarrioUFI]]] = {}
_UFI_CACHE_TTL = 300  # 5 min: Parquet is regenerated hourly, 5min is safe


def _file_age_seconds(p: Path) -> int | None:
    if not p.exists():
        return None
    return int(datetime.now(timezone.utc).timestamp() - p.stat().st_mtime)


def ufi_parquet_age() -> int | None:
    return _file_age_seconds(settings.ufi_parquet)


# ---------------------------------------------------------------------------
# Schema validation (P6)
# ---------------------------------------------------------------------------

def validate_parquet_schema() -> list[str]:
    """Returns list of missing columns. Empty list = OK or parquet not found."""
    if not settings.ufi_parquet.exists():
        return []
    try:
        con = duckdb.connect()
        cols = {
            row[0]
            for row in con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)", [str(settings.ufi_parquet)]
            ).fetchall()
        }
        con.close()
        return sorted(_REQUIRED_PARQUET_COLS - cols)
    except Exception as exc:
        logger.warning("Could not validate Parquet schema: %s", exc)
        return []


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def load_barrios_geojson() -> dict:
    if settings.barrios_geojson.exists():
        return json.loads(settings.barrios_geojson.read_text(encoding="utf-8"))
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"barrio_id": bid, "barrio_name": f"Barrio {bid}"},
                "geometry": None,
            }
            for bid in DUMMY_BARRIOS
        ],
    }


def load_tramos_geojson() -> dict:
    if settings.tramos_geojson.exists():
        return json.loads(settings.tramos_geojson.read_text(encoding="utf-8"))
    return {"type": "FeatureCollection", "features": []}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _barrio_names_from_geojson() -> dict[str, str]:
    geojson = load_barrios_geojson()
    return {
        f["properties"]["barrio_id"]: f["properties"].get("barrio_name", f["properties"]["barrio_id"])
        for f in geojson.get("features", [])
        if f.get("properties", {}).get("barrio_id")
    }


def _apply_weights(scores: dict[str, float], weights: dict[str, float]) -> tuple[float, list[FamilyContribution]]:
    ufi = sum(weights[f] * scores[f] for f in _FAMILIES) * 100
    contribs = [
        FamilyContribution(
            family=f,
            score=scores[f],
            weight=weights[f],
            contribution_pct=(weights[f] * scores[f] * 100 / max(ufi, 1e-6)) * 100,
        )
        for f in _FAMILIES
    ]
    return round(ufi, 1), contribs


# ---------------------------------------------------------------------------
# UFI desde Parquet (DuckDB) con fallback stub + TTL cache (P4)
# ---------------------------------------------------------------------------

def _load_ufi_from_parquet(at: datetime, mode: Mode) -> list[BarrioUFI] | None:
    """Lee el Parquet con DuckDB. Devuelve None si el fichero no existe o falla."""
    if not settings.ufi_parquet.exists():
        return None

    weights = MODES[mode].weights
    names = _barrio_names_from_geojson()
    hour_iso = at.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    parquet_path = str(settings.ufi_parquet)

    try:
        con = duckdb.connect()  # in-memory; read_only=True is for .duckdb files, not parquet
        rows = con.execute(
            """
            SELECT barrio_id,
                   score_trafico, score_accidentes, score_aire,
                   score_meteo, score_sensibilidad
            FROM read_parquet(?)
            WHERE date_trunc('hour', timestamp) = ?::TIMESTAMP
            """,
            [parquet_path, hour_iso],
        ).fetchall()

        if not rows:
            rows = con.execute(
                """
                SELECT barrio_id,
                       score_trafico, score_accidentes, score_aire,
                       score_meteo, score_sensibilidad
                FROM read_parquet(?)
                ORDER BY abs(epoch(timestamp) - epoch(?::TIMESTAMP))
                LIMIT 73
                """,
                [parquet_path, hour_iso],
            ).fetchall()
        con.close()
    except Exception as exc:
        logger.warning("DuckDB read failed, falling back to stub: %s", exc)
        return None

    if not rows:
        return None

    out: list[BarrioUFI] = []
    for row in rows:
        bid, s_tr, s_ac, s_ai, s_me, s_se = row
        scores = {
            "trafico": float(s_tr),
            "accidentes": float(s_ac),
            "aire": float(s_ai),
            "meteo": float(s_me),
            "sensibilidad": float(s_se),
        }
        ufi, contribs = _apply_weights(scores, weights)
        out.append(
            BarrioUFI(
                barrio_id=bid,
                barrio_name=names.get(bid, bid),
                ufi=ufi,
                contribuciones=contribs,
            )
        )
    return out


def _load_ufi_stub(at: datetime, mode: Mode) -> list[BarrioUFI]:
    weights = MODES[mode].weights
    names = _barrio_names_from_geojson()
    out: list[BarrioUFI] = []
    for bid in DUMMY_BARRIOS:
        rng = random.Random(f"{bid}-{at.isoformat()}-{mode}")
        scores = {f: rng.random() for f in _FAMILIES}
        ufi, contribs = _apply_weights(scores, weights)
        out.append(
            BarrioUFI(
                barrio_id=bid,
                barrio_name=names.get(bid, f"Barrio {bid}"),
                ufi=ufi,
                contribuciones=contribs,
            )
        )
    return out


def load_ufi(at: datetime, mode: Mode) -> list[BarrioUFI]:
    at_rounded = at.replace(minute=0, second=0, microsecond=0)
    cache_key = f"{at_rounded.isoformat()}:{mode}"
    now = time.monotonic()

    if cache_key in _ufi_cache:
        ts, data = _ufi_cache[cache_key]
        if now - ts < _UFI_CACHE_TTL:
            return data

    result = _load_ufi_from_parquet(at_rounded, mode) or _load_ufi_stub(at_rounded, mode)
    _ufi_cache[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# Tramos
# ---------------------------------------------------------------------------

def load_tramos_state(at: datetime) -> list[TramoState]:
    """Stub determinista hasta que C entregue trafico procesado."""
    out: list[TramoState] = []
    for tid in range(1, 531):
        rng = random.Random(f"tram-{tid}-{at.isoformat()}")
        out.append(TramoState(tram_id=tid, state=rng.randint(1, 6)))
    return out


# ---------------------------------------------------------------------------
# Detalle de barrio
# ---------------------------------------------------------------------------

def load_barrio_detail(barrio_id: str, at: datetime, mode: Mode) -> BarrioDetail | None:
    barrio = next((b for b in load_ufi(at, mode) if b.barrio_id == barrio_id), None)
    if barrio is None:
        return None
    rng = random.Random(f"raw-{barrio_id}-{at.isoformat()}")
    raw: dict[str, float | int | str | None] = {
        "temperature_2m": round(15 + rng.random() * 15, 1),
        "precipitation_mm": round(rng.random() * 3, 2),
        "pm2_5": round(5 + rng.random() * 40, 1),
        "no2": round(20 + rng.random() * 60, 1),
        "tramos_state_median": rng.randint(1, 6),
    }
    return BarrioDetail(
        barrio_id=barrio.barrio_id,
        barrio_name=barrio.barrio_name,
        at=at,
        mode=mode,
        ufi=barrio.ufi,
        contribuciones=barrio.contribuciones,
        raw=raw,
    )
