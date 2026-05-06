# Persona C — Datos & ML

**Tu carpeta**: `data-ml/`
**Tu output crítico**: `data/processed/ufi_latest.parquet` — sin esto, B sirve stubs y A ve datos falsos.
**Tu contrato con B**: schema fijo del Parquet. Definido en [ml/score.py](ml/score.py). NO romper sin avisar.

---

## Tu rol en el equipo

Eres el cerebro de los datos. Ingestas, limpias, entrenas, produces el Parquet que alimenta toda la app. Cuanto antes esté corriendo `python -m ml.score`, mejor para todos.

---

## Stack

| Herramienta | Para qué |
|---|---|
| pandas + geopandas | Manipulación de datos tabulares y espaciales |
| LightGBM | Modelo accidentes (Poisson) + modelo congestión (regresor) |
| scikit-learn | Preprocessing, métricas |
| DuckDB | Queries analíticas sobre Parquet |
| python-holidays | Festivos catalanes |
| requests / httpx | Descargar Open-Meteo para 73 puntos |

---

## Comandos

```powershell
# Desde la carpeta data-ml/
pip install -e ".[dev]"

# Ingesta base (hospitales, TRAMS, meteo/aire single-point)
python -m data.ingest

# Entrenar modelos (cuando tengas los datos)
python -m ml.train_accidentes
python -m ml.train_trafico

# Generar Parquet UFI (stub o real)
python -m ml.score

# Exploración
jupyter notebook notebooks/00_exploracion.ipynb
```

---

## Estructura de ficheros

```
data-ml/
  data/
    paths.py     Constantes de rutas + bbox BCN (41.31–41.47, 2.05–2.23).
    ingest.py    Pipeline ingesta: hospitales clean, TRAMS, meteo, aire.
  ml/
    score.py     Fusión → ufi_latest.parquet. SCHEMA FIJO.
    train_accidentes.py  LightGBM Poisson. STUB — completar.
    train_trafico.py     LightGBM lags. STUB — completar.
    models/      .joblib serializados (en .gitignore).
  notebooks/
    00_exploracion.ipynb  Exploración de los 4 CSVs ya en repo.
  tasks.md        ← TU LISTA DE TAREAS (empieza aquí)
  skills.md       ← Subagentes y skills útiles
```

---

## Datos de partida (ya en raíz del repo)

| Fichero | Contenido | Estado |
|---|---|---|
| `aire.csv` | Open-Meteo AQ single-point: `time, pm10, nitrogen_dioxide` | Listo |
| `meteo.csv` | Open-Meteo Forecast single-point: `time, temperature_2m, precipitation` | Listo |
| `hospitales.csv` | Overpass dump SUCIO (incluye nodos fuera de BCN) | **Limpiar primero** |
| `trafico_mayo_2026.csv` | TRAMS OD-BCN ~5 min: `idTram, data, estatActual, estatPrevist` | Listo |

Pendiente de subir antes del viernes: **dataset Kaggle de accidentes**.

---

## Schema fijo del Parquet de salida (B lo lee — NO romper)

```
barrio_id: str           (ej: "BAR-001"…"BAR-073")
timestamp: datetime      (UTC, hora redondeada)
ufi_default: float       (0-100)
score_trafico: float     (0-1)
score_accidentes: float  (0-1)
score_aire: float        (0-1)
score_meteo: float       (0-1)
score_sensibilidad: float (0-1)
```

B aplica los pesos del modo on-the-fly. Tú generas los scores crudos.

---

## Riesgo conocido: mapping distrito → barrio

El Kaggle tiene accidentes por distrito (10 distritos) y tú necesitas barrio (73). Estrategia:
1. Explorar `value_counts()` del campo de distrito en el Kaggle.
2. Crear `data/processed/mapping_districts.csv` manual con columnas `distrito_nombre | barrio_id | barrio_nombre`.
3. Proxy: `score_barrio = score_distrito × (calles_principales_barrio / max_calles_distrito)`.

**Empieza por esto antes de tocar ningún modelo.**

---

## Subagents que puedes pedir a Claude Code

Ver [skills.md](skills.md). Resumen:
- `general-purpose` → *"Escribe el feature engineering completo para LightGBM Poisson sobre el dataset Kaggle de accidentes"*
- `Explore` → *"¿Qué parámetros de LightGBM son clave para objective='poisson' en datasets pequeños?"*
- `Plan` → antes de cambiar el schema del Parquet (impacto en B)
- `claude-code-guide` → dudas de pandas, geopandas, DuckDB
