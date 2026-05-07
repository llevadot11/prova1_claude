"""Construye barrios.geojson y tramos.geojson desde las fuentes raw.

Barrios: convierte lista JSON con WKT → GeoJSON FeatureCollection válido.
Tramos:  convierte CSV con coordenadas alternadas → GeoJSON FeatureCollection.
"""
from __future__ import annotations

import json
import re
import logging
from pathlib import Path

import pandas as pd

from data.paths import PROCESSED, BARRIOS_GEOJSON, TRAMOS_GEOJSON

REPO_ROOT = Path(__file__).resolve().parents[2]
BARRIOS_RAW = PROCESSED / "barrios_raw.geojson"
TRAMOS_CSV = REPO_ROOT / "data" / "raw" / "transit_relacio_trams.csv"

log = logging.getLogger(__name__)


def _wkt_polygon_to_coords(wkt: str) -> list[list[list[float]]]:
    """Extrae coordenadas de un WKT POLYGON en WGS84.

    WKT format: POLYGON ((lon lat, lon lat, ...))
    Cada par lon lat separado por espacio; pares separados por coma.
    """
    inner = re.search(r"POLYGON\s*\(\((.*?)\)\)", wkt, re.DOTALL)
    if not inner:
        return []
    pts_str = inner.group(1).strip()
    ring = []
    for pair in pts_str.split(","):
        pair = pair.strip()
        if not pair:
            continue
        parts = pair.split()
        if len(parts) >= 2:
            try:
                ring.append([float(parts[0]), float(parts[1])])
            except ValueError:
                pass
    # GeoJSON requiere que el anillo esté cerrado (primer == último punto)
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    return [ring]


def build_barrios_geojson() -> None:
    """Convierte barrios_raw.geojson (lista WKT) → GeoJSON FeatureCollection."""
    with open(BARRIOS_RAW, encoding="utf-8") as f:
        raw = json.load(f)

    # raw es una lista de 73 dicts con codi_barri, nom_barri, geometria_wgs84
    # Ordenar por (codi_districte, codi_barri) para asignar barrio_id global 1-73
    raw_sorted = sorted(raw, key=lambda r: (int(r["codi_districte"]), int(r["codi_barri"])))

    features = []
    for idx, item in enumerate(raw_sorted, start=1):
        barrio_id = f"BAR-{idx:03d}"
        coords = _wkt_polygon_to_coords(item.get("geometria_wgs84", ""))
        feature = {
            "type": "Feature",
            "properties": {
                "barrio_id": barrio_id,
                "codi_barri": item["codi_barri"],
                "nom_barri": item["nom_barri"],
                "codi_districte": item["codi_districte"],
                "nom_districte": item["nom_districte"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": coords,
            },
        }
        features.append(feature)

    fc = {"type": "FeatureCollection", "features": features}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(BARRIOS_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)

    log.info("barrios.geojson escrito: %d features", len(features))

    # Guardar también el mapping codi_barri → barrio_id para uso posterior
    mapping = [
        {
            "barrio_id": f["properties"]["barrio_id"],
            "codi_barri": f["properties"]["codi_barri"],
            "codi_districte": f["properties"]["codi_districte"],
            "nom_barri": f["properties"]["nom_barri"],
            "nom_districte": f["properties"]["nom_districte"],
        }
        for f in features
    ]
    mapping_df = pd.DataFrame(mapping)
    mapping_df.to_csv(PROCESSED / "mapping_barrios.csv", index=False)
    log.info("mapping_barrios.csv escrito: %d filas", len(mapping_df))


def build_tramos_geojson() -> None:
    """Convierte CSV de tramos con coordenadas → GeoJSON FeatureCollection."""
    df = pd.read_csv(TRAMOS_CSV, encoding="utf-8")
    # Columnas: Tram, Descripció, Coordenades
    # Coordenades: lon1,lat1,lon2,lat2,...

    features = []
    for _, row in df.iterrows():
        tram_id = int(row.iloc[0])
        description = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
        coords_str = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""

        # Parsear coordenadas alternadas lon,lat
        parts = [float(x) for x in coords_str.split(",") if x.strip()]
        coords = [[parts[i], parts[i + 1]] for i in range(0, len(parts) - 1, 2)]

        if len(coords) < 2:
            # Tramo con coordenadas insuficientes → punto único
            if len(coords) == 1:
                geom = {"type": "Point", "coordinates": coords[0]}
            else:
                geom = {"type": "LineString", "coordinates": [[0, 0], [0, 0]]}
        else:
            geom = {"type": "LineString", "coordinates": coords}

        feature = {
            "type": "Feature",
            "properties": {
                "idTram": tram_id,
                "description": description,
            },
            "geometry": geom,
        }
        features.append(feature)

    fc = {"type": "FeatureCollection", "features": features}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(TRAMOS_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)

    log.info("tramos.geojson escrito: %d features", len(features))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_barrios_geojson()
    build_tramos_geojson()
    print("GeoJSONs generados OK")


if __name__ == "__main__":
    main()
