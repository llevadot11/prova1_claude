"""Ingesta. Punto de entrada del pipeline de datos.

Pasos:
1. Limpia hospitales.csv (filtra por bbox BCN).
2. Carga TRAMS y normaliza tipos.
3. Carga meteo + aire single-point como baseline.
4. Carga y limpia dataset de accidentes.
5. GeoJSONs ya generados por data.build_geojsons (correr separado).
6. Meteo+AQ 73 puntos ya generados por data.ingest_73points (correr separado).
"""
from __future__ import annotations

import ast
import logging

import pandas as pd

from data.paths import (
    HOSPITALES_CLEAN,
    PROCESSED,
    RAW_ACCIDENTES,
    RAW_AIRE,
    RAW_HOSPITALES,
    RAW_METEO,
    RAW_TRAFICO,
    TRAFICO_PARQUET,
    ACCIDENTES_PARQUET,
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
    log.info("Trafico: %d filas, %d tramos", len(df), df["idTram"].nunique())
    return df


def load_meteo_baseline() -> pd.DataFrame:
    df = pd.read_csv(RAW_METEO, parse_dates=["time"])
    log.info("Meteo single-point: %d horas", len(df))
    return df


def load_aire_baseline() -> pd.DataFrame:
    df = pd.read_csv(RAW_AIRE, parse_dates=["time"])
    log.info("Aire single-point: %d horas", len(df))
    return df


def load_accidentes() -> pd.DataFrame:
    """Carga y limpia el dataset de accidentes BCN (2010-2021)."""
    df = pd.read_csv(RAW_ACCIDENTES, encoding="utf-8", low_memory=False)
    # Filtrar filas con neighborhood_id válido (1-73)
    df["neighborhood_id"] = pd.to_numeric(df["neighborhood_id"], errors="coerce")
    df = df[df["neighborhood_id"] > 0].copy()
    # barrio_id global
    df["barrio_id"] = "BAR-" + df["neighborhood_id"].astype(int).astype(str).str.zfill(3)
    # Timestamp (year, month, day, hour ya están en columnas)
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").fillna(0).astype(int)
    for col in ["year", "month", "day"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["year", "month", "day"])
    df["timestamp"] = pd.to_datetime(
        dict(year=df["year"].astype(int), month=df["month"].astype(int),
             day=df["day"].astype(int), hour=df["hour"])
    )
    out = df[["barrio_id", "timestamp", "n_deaths", "n_wounded_mild",
              "n_wounded_severe", "n_victims", "n_vehicles"]].copy()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_parquet(ACCIDENTES_PARQUET, index=False)
    log.info("Accidentes: %d filas, %d barrios, rango %s-%s",
             len(out), out["barrio_id"].nunique(),
             out["timestamp"].dt.year.min(), out["timestamp"].dt.year.max())
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    clean_hospitales()
    load_trafico()
    load_meteo_baseline()
    load_aire_baseline()
    load_accidentes()
    print("Ingesta base completada. Pendientes: build_geojsons, ingest_73points, ingest_pois.")


if __name__ == "__main__":
    main()
