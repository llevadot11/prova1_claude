"""Lectura de Parquet/GeoJSON en disco. Stub: devuelve dummy si no hay ficheros aún.

Persona C es la propietaria del schema real. La forma actual aquí es la que
asume el contrato de la API y debe coincidir con el output de
`packages.ml.score`.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.modes import MODES
from app.schemas import (
    BarrioDetail,
    BarrioUFI,
    FamilyContribution,
    Mode,
    TramoState,
)

# 73 barrios reales de Barcelona — placeholder hasta que C suba el GeoJSON.
DUMMY_BARRIOS = [f"BAR-{i:03d}" for i in range(1, 74)]


def _file_age_seconds(p: Path) -> int | None:
    if not p.exists():
        return None
    return int(datetime.now(timezone.utc).timestamp() - p.stat().st_mtime)


def ufi_parquet_age() -> int | None:
    return _file_age_seconds(settings.ufi_parquet)


def load_barrios_geojson() -> dict:
    if settings.barrios_geojson.exists():
        return json.loads(settings.barrios_geojson.read_text(encoding="utf-8"))
    # Stub vacío con 73 features sin geometría.
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


def load_ufi(at: datetime, mode: Mode) -> list[BarrioUFI]:
    """Lee `data/processed/ufi_latest.parquet` filtrado por hora más cercana.
    Stub determinista por (barrio_id, hora) hasta que C entregue el Parquet.
    """
    if settings.ufi_parquet.exists():
        # TODO C: leer con DuckDB
        # con = duckdb.connect(str(settings.ufi_parquet), read_only=True)
        # ...
        pass

    families = ("trafico", "accidentes", "aire", "meteo", "sensibilidad")
    weights = MODES[mode].weights
    out: list[BarrioUFI] = []
    for bid in DUMMY_BARRIOS:
        rng = random.Random(f"{bid}-{at.isoformat()}-{mode}")
        scores = {f: rng.random() for f in families}
        ufi = sum(weights[f] * s for f, s in scores.items()) * 100
        contribs = [
            FamilyContribution(
                family=f,
                score=scores[f],
                weight=weights[f],
                contribution_pct=(weights[f] * scores[f] * 100 / max(ufi, 1e-6)) * 100,
            )
            for f in families
        ]
        out.append(
            BarrioUFI(
                barrio_id=bid,
                barrio_name=f"Barrio {bid}",
                ufi=round(ufi, 1),
                contribuciones=contribs,
            )
        )
    return out


def load_tramos_state(at: datetime) -> list[TramoState]:
    """Stub: estado aleatorio determinista por (tram_id, hora) hasta C."""
    out: list[TramoState] = []
    for tid in range(1, 531):
        rng = random.Random(f"tram-{tid}-{at.isoformat()}")
        out.append(TramoState(tram_id=tid, state=rng.randint(1, 6)))
    return out


def load_barrio_detail(barrio_id: str, at: datetime, mode: Mode) -> BarrioDetail | None:
    barrio = next((b for b in load_ufi(at, mode) if b.barrio_id == barrio_id), None)
    if barrio is None:
        return None
    rng = random.Random(f"raw-{barrio_id}-{at.isoformat()}")
    raw = {
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
