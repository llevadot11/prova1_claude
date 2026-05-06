from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"
CACHE = REPO_ROOT / "data" / "cache"

# CSVs ya en el repo (raíz a fecha de scaffold).
RAW_AIRE = REPO_ROOT / "aire.csv"
RAW_METEO = REPO_ROOT / "meteo.csv"
RAW_HOSPITALES = REPO_ROOT / "hospitales.csv"
RAW_TRAFICO = REPO_ROOT / "trafico_mayo_2026.csv"

# Outputs.
BARRIOS_GEOJSON = PROCESSED / "barrios.geojson"
TRAMOS_GEOJSON = PROCESSED / "tramos.geojson"
HOSPITALES_CLEAN = PROCESSED / "hospitales_bcn.parquet"
TRAFICO_PARQUET = PROCESSED / "trafico.parquet"
ACCIDENTES_PARQUET = PROCESSED / "accidentes.parquet"
UFI_PARQUET = PROCESSED / "ufi_latest.parquet"

# Bounding box Barcelona ciudad para filtrar Overpass dump.
BCN_BBOX = (41.31, 41.47, 2.05, 2.23)  # (min_lat, max_lat, min_lon, max_lon)
