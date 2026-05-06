# packages/ — Datos y ML

Dos sub-paquetes Python:

```
packages/
  pyproject.toml    Dependencias compartidas (pandas, lightgbm, geopandas, duckdb).
  data/             Ingesta y limpieza.
    paths.py        Constantes de rutas y bbox BCN.
    ingest.py       Pipeline de carga: hospitales, TRAMS, meteo, aire.
  ml/               Entrenamiento + scoring.
    score.py        Pipeline de fusión → ufi_latest.parquet (entry point B).
    train_accidentes.py   LightGBM Poisson sobre Kaggle.
    train_trafico.py      LightGBM lags sobre TRAMS.
    models/         joblib serializados (en .gitignore).
```

## Comandos

```powershell
# Desde raíz del repo
pip install -e ./packages

python -m packages.data.ingest
python -m packages.ml.train_accidentes
python -m packages.ml.train_trafico
python -m packages.ml.score
```

## Reglas duras

- **NO** poner credenciales en código. Todo en `.env` raíz.
- **NO** modificar `data/raw/`. Es read-only.
- Schema de salida de `score.py` está fijado en su docstring: 5 columnas `score_<familia>` (0–1) crudas, ufi_default, barrio_id, timestamp. Backend aplica los pesos del modo on-the-fly. Si añades familias, **avisa a B**.
- Validación de modelos: split temporal estricto. Nunca aleatorio.
- POIs OSM se descargan UNA vez y se cachean en `data/processed/pois.parquet`. No martillear Overpass.

## Tareas Persona C

- [ ] Limpiar `hospitales.csv` filtrando bbox BCN (ya stub en `ingest.py`).
- [ ] Descargar GeoJSON 73 barrios de Open Data BCN → `data/processed/barrios.geojson`.
- [ ] Descargar GeoJSON tramos viarios → `data/processed/tramos.geojson`.
- [ ] Mapear tramos → barrio (centroide del tramo dentro de polígono barrio).
- [ ] Extender `csv_import.py` raíz a 73 puntos meteo+AQ.
- [ ] Cargar dataset Kaggle accidentes a `data/processed/accidentes.parquet` con mapping distrito↔barrio.
- [ ] Entrenar LightGBM Poisson accidentes.
- [ ] Entrenar LightGBM lags TRAMS.
- [ ] Reemplazar `heuristic_scores()` en `score.py` con lógica real.

## Riesgo conocido

El mapping distrito↔barrio del Kaggle es ambiguo (tildes, nombres en catalán y castellano). **Empezar por aquí** — sin esto, los modelos no se pueden integrar.
