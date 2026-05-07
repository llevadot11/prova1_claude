"""Genera mapping idTram → barrio_id usando sjoin espacial de geopandas.

Estrategia: centroide de cada LineString de tramo dentro del polígono del barrio.
Si el centroide cae fuera de todos los barrios (tramo en el límite), busca el
barrio más cercano.

Output: data/processed/tramo_barrio.parquet
  idTram: int
  barrio_id: str  (BAR-001…BAR-073)
  nom_barri: str
"""
from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

from data.paths import PROCESSED, TRAMOS_GEOJSON, BARRIOS_GEOJSON

log = logging.getLogger(__name__)

TRAMO_BARRIO_PARQUET = PROCESSED / "tramo_barrio.parquet"


def build_tramo_barrio_mapping() -> pd.DataFrame:
    # Cargar barrios
    barrios = gpd.read_file(BARRIOS_GEOJSON)
    barrios = barrios.set_crs(epsg=4326)

    # Cargar tramos y calcular centroides
    tramos = gpd.read_file(TRAMOS_GEOJSON)
    tramos = tramos.set_crs(epsg=4326)

    # Centroides de los tramos
    tramos_pts = tramos.copy()
    tramos_pts["geometry"] = tramos.geometry.centroid

    # Sjoin: centroide dentro del polígono del barrio
    joined = gpd.sjoin(
        tramos_pts[["idTram", "geometry"]],
        barrios[["barrio_id", "nom_barri", "geometry"]],
        how="left",
        predicate="within",
    )

    # Para tramos sin barrio (centroides fuera de todos los polígonos), usar nearest
    missing_mask = joined["barrio_id"].isna()
    n_missing = missing_mask.sum()
    if n_missing > 0:
        log.warning("%d tramos sin barrio por sjoin, usando nearest", n_missing)
        missing_tramos = tramos_pts.loc[tramos_pts["idTram"].isin(joined.loc[missing_mask, "idTram"])]
        nearest = gpd.sjoin_nearest(
            missing_tramos[["idTram", "geometry"]],
            barrios[["barrio_id", "nom_barri", "geometry"]],
            how="left",
        )
        joined = joined.dropna(subset=["barrio_id"])
        joined = pd.concat([joined, nearest], ignore_index=True)

    result = (
        joined[["idTram", "barrio_id", "nom_barri"]]
        .drop_duplicates(subset=["idTram"])
        .reset_index(drop=True)
    )
    result["idTram"] = result["idTram"].astype(int)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    result.to_parquet(TRAMO_BARRIO_PARQUET, index=False)
    log.info(
        "tramo_barrio.parquet: %d tramos → %d barrios únicos",
        len(result),
        result["barrio_id"].nunique(),
    )
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = build_tramo_barrio_mapping()
    print(f"Mapping generado: {len(df)} tramos")
    print(df.groupby("barrio_id").size().sort_values(ascending=False).head(10))


if __name__ == "__main__":
    main()
