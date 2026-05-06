# UFI Barcelona — Urban Friction Index

App que responde *"¿Qué zonas de Barcelona estarán peor para moverse hoy/mañana y por qué?"* combinando tráfico, meteo, calidad del aire, accidentes históricos y POIs en un índice 0–100 por barrio·hora con explicación natural.

## Stack global

| Capa | Tecnología |
|---|---|
| Front | React + Vite + TS + MapLibre + deck.gl + Tailwind + Zustand |
| API | FastAPI + httpx + Pydantic |
| ML / datos | pandas + geopandas + LightGBM + scikit-learn + DuckDB |
| Storage | DuckDB sobre Parquet en disco + SQLite (cache) |
| LLM | Anthropic SDK con `claude-haiku-4-5-20251001`, prompt caching activo |
| Infra | docker-compose (local) + Vercel (front) + Railway (API) |

## Layout

```
apps/web/         React + Vite (puerto 3000)
apps/api/         FastAPI (puerto 8000)
packages/data/    ingesta: extiende csv_import.py, descarga GeoJSON, limpia hospitales
packages/ml/      entrenamiento + scoring → data/processed/ufi_latest.parquet
notebooks/        exploración y validación
data/raw/         CSVs originales (ya hay 4)
data/processed/   Parquets cocinados, ufi_latest.parquet
data/cache/       SQLite cache APIs externas
infra/            docker-compose, deploy
demo/             snapshots fallback, guion
```

## Datos ya en repo (data/raw/ o raíz, según ingesta)

- `aire.csv` — single-point Open-Meteo AQ (lat 41.3888, lon 2.159). Hay que ampliar a 73 puntos.
- `meteo.csv` — single-point Open-Meteo Forecast. Idem.
- `hospitales.csv` — Overpass dump SUCIO (incluye Granollers y hasta Venezuela). **Hay que filtrar por bbox BCN antes de usar.**
- `trafico_mayo_2026.csv` — TRAMS OD-BCN (~46 MB), `idTram, data, estatActual, estatPrevist`. Cada ~5 min.
- `csv_import.py` — script de descarga ya escrito, hay que extenderlo.

Pendientes de subir antes del kickoff: dataset Kaggle accidentes, GeoJSON 73 barrios, GeoJSON tramos viarios.

## Contrato de endpoints (cerrado vie 19:00)

```
GET /barrios                          → GeoJSON 73 barrios
GET /tramos                           → GeoJSON tramos viarios
GET /ufi?at=<iso>&mode=default        → [{barrio_id, ufi, contribuciones}]
GET /tramos/state?at=<iso>            → [{tram_id, state}]
GET /barrio/{id}?at=<iso>&mode=...    → detalle con valores crudos
GET /explain/{id}?at=<iso>&mode=...   → frase natural cacheada
GET /modes                            → [default, familiar, runner, movilidad_reducida]
GET /health                           → status APIs upstream
```

## Convenciones

- Lengua de los identificadores: inglés. Lengua de los textos al usuario: castellano.
- Timestamps en ISO 8601 UTC en la API; conversión a `Europe/Madrid` solo en el front.
- Todo path absoluto en código; nunca `os.chdir()`.
- DuckDB se abre en modo solo-lectura desde el API.
- Anthropic SDK SIEMPRE con `cache_control` sobre el system prompt fijo.
- Modelos guardados en `packages/ml/models/*.joblib` (en `.gitignore`).

## Comandos clave

```powershell
# Backend
cd apps/api; uvicorn app.main:app --reload --port 8000

# Frontend
cd apps/web; npm run dev

# Ingesta + scoring (manual)
python -m packages.data.ingest
python -m packages.ml.score

# Tests
cd apps/api; pytest
cd apps/web; npm test

# Demo offline (lee snapshot)
$env:DEMO_OFFLINE=1; uvicorn app.main:app --port 8000
```

## Roles

- **A — Frontend** (`apps/web/`): mapa, slider, panel, modos, animaciones.
- **B — Backend** (`apps/api/`): API, cache, DuckDB, wrapper Claude.
- **C — Datos/ML** (`packages/data/`, `packages/ml/`, `notebooks/`): ingesta, modelos, fusión UFI.
- **D — Demo Master + DevOps**: docker, Vercel/Railway, snapshot fallback, guion demo, QA cruzado.

## Hitos

- **H0 vie 22:00**: front pinta 73 polígonos coloreados aleatorios desde el back.
- **H1 sáb 14:00**: UFI heurístico end-to-end con datos reales + URL pública navegable.
- **H2 sáb 22:00**: explicaciones naturales y modos. **Snapshot fallback generado.**
- **Freeze dom 14:00**: solo bugs. 3 ensayos cronometrados de demo.

## Plan completo

Ver `C:\Users\matia\.claude\plans\contexto-somos-un-cuddly-pnueli.md`.
