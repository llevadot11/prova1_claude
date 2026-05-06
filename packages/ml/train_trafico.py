"""Entrena LightGBM con lags 1h/24h/168h sobre TRAMS por tramo.

STUB: persona C completa. Test con últimos 7 días. Output: models/trafico.joblib.
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError(
        "Pendiente: cargar trafico.parquet, generar lags por idTram, "
        "LightGBM regresor, split temporal, joblib.dump."
    )


if __name__ == "__main__":
    main()
