"""Ingesta. Punto de entrada del pipeline de datos.

Pasos:
1. Limpia hospitales.csv (filtra por bbox BCN).
2. Carga TRAMS y normaliza tipos.
3. Carga meteo + aire single-point como baseline.
4. (TODO) Descarga Open-Meteo Forecast + AQ para 73 centroides de barrio.
5. (TODO) Descarga GeoJSON 73 barrios y tramos viarios de Open Data BCN.
6. (TODO) Carga dataset Kaggle accidentes.

Persona C: completa los TODO. Cada paso debe escribir a `data/processed/`.
"""
from __future__ import annotations

import ast
import logging

import pandas as pd

from data.paths import (
    HOSPITALES_CLEAN,
    PROCESSED,
    RAW_AIRE,
    RAW_HOSPITALES,
    RAW_METEO,
    RAW_TRAFICO,
    TRAFICO_PARQUET,
    BCN_BBOX,
)

log = logging.getLogger(__name__)


def clean_hospitales() -> pd.DataFrame:
    """El dump de Overpass incluye Granollers, Venezuela, etc. Filtrar a BCN."""
    df = pd.read_csv(RAW_HOSPITALES)
    min_lat, max_lat, min_lon, max_lon = BCN_BBOX
    in_bcn = (
        df["lat"].between(min_lat, max_lat) & df["lon"].between(min_lon, max_lon)
    )
    bcn = df.loc[in_bcn].copy()

    def parse_tags(s: str) -> dict:
        try:
            return ast.literal_eval(s) if isinstance(s, str) else {}
        except Exception:
            return {}

    bcn["tags_dict"] = bcn["tags"].apply(parse_tags)
    bcn["name"] = bcn["tags_dict"].apply(lambda t: t.get("name"))
    bcn = bcn[["id", "lat", "lon", "name"]].dropna(subset=["name"]).reset_index(drop=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    bcn.to_parquet(HOSPITALES_CLEAN, index=False)
    log.info("Hospitales BCN: %d (de %d totales)", len(bcn), len(df))
    return bcn


def load_trafico() -> pd.DataFrame:
    """TRAMS: idTram, data (YYYYMMDDhhmmss), estatActual, estatPrevist."""
    df = pd.read_csv(RAW_TRAFICO)
    df["timestamp"] = pd.to_datetime(df["data"].astype(str), format="%Y%m%d%H%M%S")
    df = df[["idTram", "timestamp", "estatActual", "estatPrevist"]]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(TRAFICO_PARQUET, index=False)
    log.info("Tráfico: %d filas, %d tramos", len(df), df["idTram"].nunique())
    return df


def load_meteo_baseline() -> pd.DataFrame:
    df = pd.read_csv(RAW_METEO, parse_dates=["time"])
    log.info("Meteo single-point: %d horas", len(df))
    return df


def load_aire_baseline() -> pd.DataFrame:
    df = pd.read_csv(RAW_AIRE, parse_dates=["time"])
    log.info("Aire single-point: %d horas", len(df))
    return df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    clean_hospitales()
    load_trafico()
    load_meteo_baseline()
    load_aire_baseline()
    print("✅ Ingesta base completada. Pendientes: 73-points meteo/AQ, GeoJSONs, Kaggle.")


if __name__ == "__main__":
    main()
