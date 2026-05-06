"""Pipeline de scoring → data/processed/ufi_latest.parquet.

Salida (schema fijo, NO romper sin avisar a B):
    barrio_id: str
    timestamp: datetime (UTC, hora redondeada)
    ufi_default: float (0-100)         # bajo modo default
    score_trafico: float (0-1)
    score_accidentes: float (0-1)
    score_aire: float (0-1)
    score_meteo: float (0-1)
    score_sensibilidad: float (0-1)

El backend aplica los pesos de cada modo on-the-fly desde estas 5 columnas
de score crudo, así no hay que regenerar el Parquet por modo.

Persona C: rellenar implementación. El stub crea Parquet de relleno.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from data.paths import PROCESSED, UFI_PARQUET

log = logging.getLogger(__name__)

FAMILIES = ("trafico", "accidentes", "aire", "meteo", "sensibilidad")
N_BARRIOS = 73
HORIZON_HOURS = 48


def heuristic_scores() -> pd.DataFrame:
    """STUB: scores aleatorios reproducibles. Sustituir con lógica real."""
    rng = np.random.default_rng(42)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows = []
    for h in range(HORIZON_HOURS):
        ts = now + timedelta(hours=h)
        for i in range(1, N_BARRIOS + 1):
            row = {"barrio_id": f"BAR-{i:03d}", "timestamp": ts}
            for fam in FAMILIES:
                row[f"score_{fam}"] = float(rng.random())
            rows.append(row)
    return pd.DataFrame(rows)


def fuse(scores: pd.DataFrame) -> pd.DataFrame:
    """Aplica pesos default y normaliza relativo al día (z-score + sigmoide)."""
    weights = {
        "trafico": 0.30,
        "accidentes": 0.25,
        "aire": 0.20,
        "meteo": 0.15,
        "sensibilidad": 0.10,
    }
    raw = sum(weights[f] * scores[f"score_{f}"] for f in FAMILIES)
    scores = scores.assign(_raw=raw)
    # z-score por hora
    grp = scores.groupby("timestamp")["_raw"]
    z = (scores["_raw"] - grp.transform("mean")) / grp.transform("std").replace(0, 1)
    scores["ufi_default"] = (1 / (1 + np.exp(-z))) * 100
    return scores.drop(columns=["_raw"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    scores = heuristic_scores()
    out = fuse(scores)
    out.to_parquet(UFI_PARQUET, index=False)
    log.info("UFI escrito: %s (%d filas)", UFI_PARQUET, len(out))


if __name__ == "__main__":
    main()
