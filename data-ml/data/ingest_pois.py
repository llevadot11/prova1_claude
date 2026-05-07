"""Descarga POIs (hospitales + colegios) de Overpass API y genera score_sensibilidad.

Output: data/processed/pois_per_barrio.parquet
  barrio_id: str, n_hospitales: int, n_colegios: int, score_sensibilidad: float
"""
from __future__ import annotations

import json
import logging
import time

import geopandas as gpd
import pandas as pd
import requests

from data.paths import PROCESSED, BCN_BBOX

POIS_PARQUET = PROCESSED / "pois_per_barrio.parquet"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
log = logging.getLogger(__name__)


def _overpass_query(amenity: str, bbox: tuple) -> list[dict]:
    """Descarga nodos de un tipo de amenity en el bbox BCN."""
    min_lat, max_lat, min_lon, max_lon = bbox
    query = (
        f"[out:json][timeout:60];"
        f"(node[\"amenity\"=\"{amenity}\"]({min_lat},{min_lon},{max_lat},{max_lon});"
        f"way[\"amenity\"=\"{amenity}\"]({min_lat},{min_lon},{max_lat},{max_lon}););"
        f"out center;"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        r = requests.post(
            OVERPASS_URL,
            data=f"data={requests.utils.quote(query)}",
            headers=headers,
            timeout=90,
        )
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception as e:
        log.warning("Error Overpass %s: %s", amenity, e)
        return []


def _elements_to_gdf(elements: list[dict]) -> gpd.GeoDataFrame:
    rows = []
    for el in elements:
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat and lon:
            rows.append({"lat": lat, "lon": lon, "name": el.get("tags", {}).get("name", "")})
    if not rows:
        return gpd.GeoDataFrame(columns=["geometry"])
    df = pd.DataFrame(rows)
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")


def build_poi_scores() -> pd.DataFrame:
    barrios = gpd.read_file(PROCESSED / "barrios.geojson").set_crs(epsg=4326)
    all_barrios = pd.DataFrame({"barrio_id": barrios["barrio_id"].tolist()})

    log.info("Descargando hospitales de Overpass...")
    hosp_els = _overpass_query("hospital", BCN_BBOX)
    hosp_gdf = _elements_to_gdf(hosp_els)
    time.sleep(1)

    log.info("Descargando colegios de Overpass...")
    school_els = _overpass_query("school", BCN_BBOX)
    school_gdf = _elements_to_gdf(school_els)
    time.sleep(1)

    def count_pois(poi_gdf: gpd.GeoDataFrame, col: str) -> pd.DataFrame:
        if poi_gdf.empty or "geometry" not in poi_gdf.columns:
            return pd.DataFrame({"barrio_id": all_barrios["barrio_id"], col: 0})
        joined = gpd.sjoin(poi_gdf, barrios[["barrio_id", "geometry"]], how="left", predicate="within")
        counts = joined.groupby("barrio_id").size().reset_index(name=col)
        return all_barrios.merge(counts, on="barrio_id", how="left").fillna({col: 0})

    hosp_counts = count_pois(hosp_gdf, "n_hospitales")
    school_counts = count_pois(school_gdf, "n_colegios")

    result = hosp_counts.merge(school_counts, on="barrio_id")
    result["n_hospitales"] = result["n_hospitales"].astype(int)
    result["n_colegios"] = result["n_colegios"].astype(int)

    # Score: hospitales pesan 2× más que colegios (zonas hospitalarias = mayor sensibilidad)
    combined = result["n_hospitales"] * 2 + result["n_colegios"]
    max_combined = combined.max()
    if max_combined > 0:
        result["score_sensibilidad"] = (combined / max_combined).clip(0.0, 1.0)
    else:
        result["score_sensibilidad"] = 0.1

    PROCESSED.mkdir(parents=True, exist_ok=True)
    result.to_parquet(POIS_PARQUET, index=False)
    log.info(
        "POIs: %d hospitales, %d colegios, %d barrios",
        hosp_counts["n_hospitales"].sum(),
        school_counts["n_colegios"].sum(),
        len(result),
    )
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = build_poi_scores()
    print(f"POIs procesados: {len(df)} barrios")
    print(df.sort_values("score_sensibilidad", ascending=False).head(10).to_string())


if __name__ == "__main__":
    main()
