# Tareas — Persona C (Datos & ML)

> Abre esta carpeta en Claude Code con `claude` desde `data-ml/`.
> Marca cada tarea con `[x]` al terminarla.
> **PRIORITARIO**: las primeras 3 tareas desbloquean a B y a A. Hazlas primero.

---

## Bloque 1 — Viernes 19:00–22:00 (Datos base + GeoJSONs) ← CRÍTICO

- [ ] **`pip install -e ".[dev]"`**
- [ ] **Explorar los 4 CSVs** con `notebooks/00_exploracion.ipynb`:
  - Ejecutar todas las celdas
  - Confirmar nº de tramos únicos en TRAMS, rango de fechas, distribución de `estatActual`
- [ ] **Limpiar hospitales** → `data/processed/hospitales_bcn.parquet`:
  - Correr `python -m data.ingest` (ya implementado)
  - Verificar que quedan solo hospitales dentro de BCN
- [ ] **Descargar GeoJSON 73 barrios** → `data/processed/barrios.geojson`:
  - URL Open Data BCN: `https://opendata-ajuntament.barcelona.cat/data/dataset/20170706-districtes-barris`
  - Alternativa OSM/geojson.io si tarda: buscar "Barcelona neighbourhoods GeoJSON"
  - Verificar que tiene campo `barrio_id` o `barri` o `NOM` (renombrar a `barrio_id`)
- [ ] **Descargar GeoJSON tramos viarios** → `data/processed/tramos.geojson`:
  - URL Open Data BCN dataset "TRAMS - Trams de carrers" (buscar el GeoJSON de geometrías)
  - Verificar que `idTram` en el GeoJSON casa con `idTram` del CSV de tráfico
- [ ] **`python -m ml.score`** — confirmar que el stub genera `data/processed/ufi_latest.parquet`
  - Avisar a B que puede empezar a probar con este stub

---

## Bloque 2 — Sábado 09:00–14:00 (Mapping + ingesta ampliada)

- [ ] **Mapping tramo → barrio** en `data/tramo_barrio.py`:
  - Carga GeoJSON tramos + GeoJSON barrios con geopandas
  - Para cada tramo, encuentra el barrio que contiene su centroide (sjoin)
  - Guarda `data/processed/tramo_barrio.parquet` con `idTram, barrio_id, barrio_name`
- [ ] **Mapping distrito → barrio** (para el Kaggle):
  - Explorar el Kaggle: `df['nom_districte'].value_counts()` o similar
  - Crear `data/processed/mapping_districts.csv`: `distrito_nombre, barrio_id, barrio_name`
  - Proxy: `score_barrio ≈ score_distrito × (len(tramos_barrio) / max(len(tramos_barrio_en_distrito)))`
- [ ] **Ampliar ingesta meteo + AQ a 73 centroides** en `data/ingest_73points.py`:
  - Extraer centroides de los 73 barrios del GeoJSON
  - Para cada uno: `GET api.open-meteo.com/v1/forecast?lat=X&lon=Y&hourly=temperature_2m,precipitation,wind_speed_10m,humidity`
  - Para cada uno: `GET air-quality-api.open-meteo.com`
  - Guardar `data/processed/meteo_73pts.parquet` y `data/processed/aire_73pts.parquet`

---

## Bloque 3 — Sábado 09:00–22:00 (Modelos)

### Modelo congestión TRAMS (LightGBM lags)

- [ ] **Feature engineering** en `ml/features_trafico.py`:
  - Cargar `data/processed/trafico.parquet`
  - Generar lags por `idTram`: `estat_1h, estat_24h, estat_168h`
  - Features temporales: `hour, dow, month, is_holiday, is_rush_hour`
  - Join con meteo (usar single-point como proxy global)
  - Target: `estatActual` en siguiente hora
- [ ] **Entrenar** `ml/train_trafico.py`:
  - `LGBMRegressor(objective='regression_l1', n_estimators=500)`
  - Split temporal: últimos 7 días como test
  - Métricas: MAE por tramo, Spearman overall
  - Guardar `ml/models/trafico.joblib`
- [ ] **Predicción 48h**: para cada tramo, predecir `estatActual` h+1…h+48

### Modelo accidentes (LightGBM Poisson)

- [ ] **Cargar Kaggle** cuando llegue → `data/processed/accidentes.parquet`
- [ ] **Feature engineering** en `ml/features_accidentes.py`:
  - Features: `distrito_id, hour, dow, month, is_holiday, temp, precipitation, wind_speed`
  - Target: `n_accidentes`
- [ ] **Entrenar** `ml/train_accidentes.py`:
  - `LGBMRegressor(objective='poisson', n_estimators=500)`
  - Split temporal: train años n-3..n-1, test año n
  - Guardar `ml/models/accidentes.joblib`
- [ ] **Bridge a barrio**: aplicar proxy mapping distrito→barrio

### Fusión real

- [ ] **Reemplazar stub en `ml/score.py`**:
  - Cargar predicciones de congestión (modelo TRAMS) → `score_trafico`
  - Cargar predicciones de accidentes (modelo Kaggle) → `score_accidentes`
  - Cargar forecast meteo 73pts → `score_meteo`
  - Cargar forecast AQ 73pts → `score_aire`
  - Cargar densidad POIs (estático) → `score_sensibilidad`
  - Aplicar interacciones derivadas: `lluvia × hora_punta`, `mala_AQ × hora_escolar`
  - Normalizar cada familia 0–1 con min-max robusto (percentil 5–95)
  - Escribir Parquet final
- [ ] **Avisar a B** que el Parquet real está listo

---

## Bloque 4 — Domingo 09:00–14:00 (Calibración y extras)

- [ ] **Revisar distribución del UFI**: histograma por hora. ¿Hay barrios siempre en rojo?
- [ ] **Score sensibilidad estático**:
  - Para cada barrio: `(n_hospitales + 2×n_colegios) / max_barrio` normalizado
  - Usar `hospitales_bcn.parquet` + descarga colegios OSM
- [ ] **POIs colegios** si no se hizo antes:
  - `data/download_pois.py`: Overpass `amenity=school` en bbox BCN
- [ ] **Bicing disponibilidad** (stretch): Open Data BCN GBFS

---

## Criterio de "done" para la demo

- [ ] `data/processed/ufi_latest.parquet` existe y tiene 73×48 filas con los 5 scores reales
- [ ] `data/processed/barrios.geojson` tiene geometrías válidas para los 73 barrios
- [ ] `data/processed/tramos.geojson` tiene geometrías y `idTram`
- [ ] `python -m ml.score` corre en < 2 minutos
- [ ] Modelo TRAMS tiene MAE < 1.0 por tramo en los últimos 7 días
