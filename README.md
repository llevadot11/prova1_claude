# UFI Barcelona — Urban Friction Index

> ¿Qué zonas de Barcelona estarán peor para moverse hoy y por qué?

Índice 0–100 por barrio·hora combinando tráfico, meteo, calidad del aire, accidentes históricos y POIs. Explicaciones en lenguaje natural vía Claude Haiku.

## Arrancar en local (Docker)

Prerequisito: Docker Desktop corriendo.

```powershell
# 1. Copia las variables de entorno y añade tu API key de Anthropic
cp .env.example .env
# Edita .env y pon ANTHROPIC_API_KEY=sk-ant-...

# 2. Levanta backend (:8000) + frontend (:3000)
cd devops/infra
docker-compose up --build

# 3. Abre http://localhost:3000
```

## Arrancar en local (dev sin Docker)

```powershell
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000

# Pipeline de datos (Persona C)
cd data-ml
python -m data.ingest
python -m ml.score
```

## URLs públicas

| Servicio | URL |
|---|---|
| Frontend | https://ufi-barcelona.vercel.app *(se actualiza tras deploy)* |
| Backend API | https://ufi-api.up.railway.app *(se actualiza tras deploy)* |
| Docs API | `<railway-url>/docs` |

## Variables de entorno

Copia `.env.example` a `.env` y rellena:

| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | Clave de Anthropic para Claude Haiku |
| `DEMO_OFFLINE` | `1` para modo offline (sirve del snapshot sin APIs externas) |
| `VITE_API_BASE_URL` | URL del backend para Vercel (Railway URL) |

## Modo demo offline (fallback)

```powershell
$env:DEMO_OFFLINE=1
cd backend
uvicorn app.main:app --port 8000
```

El backend sirve datos del snapshot `data/processed/demo_snapshot.parquet` sin llamar a ninguna API externa ni a Claude.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite + TypeScript + MapLibre + deck.gl + Tailwind + Zustand |
| Backend | FastAPI + httpx + Pydantic v2 + DuckDB |
| ML / datos | pandas + geopandas + LightGBM + scikit-learn |
| Storage | DuckDB sobre Parquet + SQLite (cache) |
| LLM | Claude Haiku 4.5 (Anthropic) con prompt caching |
| Infra | docker-compose (local) · Vercel (frontend) · Railway (backend) |

## Estructura

```
frontend/     React + Vite + MapLibre (Persona A)
backend/      FastAPI + DuckDB + Claude (Persona B)
data-ml/      pandas + LightGBM → ufi_latest.parquet (Persona C)
devops/       Docker + Railway + Vercel + demo (Persona D)
data/
  raw/        CSVs originales (read-only)
  processed/  Parquets y GeoJSONs generados por data-ml/
  cache/      SQLite cache de APIs externas
```

## Endpoints principales

```
GET /barrios                     → GeoJSON 73 barrios de Barcelona
GET /ufi?at=<iso>&mode=default   → UFI por barrio·hora
GET /explain/{id}?at=&mode=      → Explicación en castellano (Claude)
GET /health                      → Estado de servicios upstream
GET /docs                        → Swagger UI interactivo
```
