"""Entrena LightGBM Poisson sobre dataset Kaggle de accidentes.

STUB: persona C completa. Validación con split temporal estricto
(años n-3..n-1 train, año n test). Output: models/accidentes.joblib.
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError(
        "Pendiente: cargar dataset Kaggle, feature engineering, "
        "LightGBM objective='poisson', split temporal, joblib.dump."
    )


if __name__ == "__main__":
    main()
