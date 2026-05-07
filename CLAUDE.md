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

## Layout (una carpeta por persona)

```
frontend/      ← PERSONA A  · React + Vite + MapLibre + deck.gl + Tailwind
backend/       ← PERSONA B  · FastAPI + Pydantic + DuckDB + Claude Haiku
data-ml/       ← PERSONA C  · pandas + geopandas + LightGBM → ufi_latest.parquet
devops/        ← PERSONA D  · Docker + Railway + Vercel + demo
data/
  raw/         CSVs originales (read-only para todos)
  processed/   Parquets, GeoJSONs (escribe C, leen B y D)
  cache/       SQLite cache APIs externas (escribe B)
```

Cada carpeta tiene su propio `CLAUDE.md`, `tasks.md` y `skills.md`.
Abre Claude Code desde la carpeta de tu persona: `claude` desde `frontend/`, `backend/`, etc.

## Datos ya en repo (todos en `data/raw/`)

- `data/raw/aire.csv` — single-point Open-Meteo AQ (lat 41.3888, lon 2.159).
- `data/raw/meteo.csv` — single-point Open-Meteo Forecast.
- `data/raw/hospitales.csv` — Overpass dump SUCIO. Filtrar por bbox BCN antes de usar.
- `data/raw/trafico_mayo_2026.csv` — TRAMS OD-BCN (~46 MB), `idTram, data, estatActual, estatPrevist`.
- `data/raw/accidents_opendata.csv` — Accidentes BCN (~24 MB).
- `data-ml/data/csv_import.py` — script de descarga.

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
- Modelos guardados en `data-ml/ml/models/*.joblib` (en `.gitignore`).

## Comandos clave

```powershell
# Backend (Persona B)
cd backend; uvicorn app.main:app --reload --port 8000

# Frontend (Persona A)
cd frontend; npm run dev

# Ingesta + scoring (Persona C)
cd data-ml; python -m data.ingest; python -m ml.score

# Tests (Persona B)
cd backend; pytest

# Docker local (Persona D)
cd devops/infra; docker-compose up --build

# Demo offline (Persona D)
$env:DEMO_OFFLINE=1; cd backend; uvicorn app.main:app --port 8000
```

## Roles

- **A — Frontend** (`frontend/`): mapa, slider, panel, modos, animaciones.
- **B — Backend** (`backend/`): API, cache, DuckDB, wrapper Claude.
- **C — Datos/ML** (`data-ml/`): ingesta, modelos, fusión UFI → Parquet.
- **D — Demo Master + DevOps** (`devops/`): docker, Vercel/Railway, snapshot fallback, guion demo, QA cruzado.

## Hitos

- **H0 vie 22:00**: front pinta 73 polígonos coloreados aleatorios desde el back.
- **H1 sáb 14:00**: UFI heurístico end-to-end con datos reales + URL pública navegable.
- **H2 sáb 22:00**: explicaciones naturales y modos. **Snapshot fallback generado.**
- **Freeze dom 14:00**: solo bugs. 3 ensayos cronometrados de demo.

## Plan completo

Ver `C:\Users\matia\.claude\plans\contexto-somos-un-cuddly-pnueli.md`.
