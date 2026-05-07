# UFI Barcelona — Urban Friction Index

> ¿Qué zonas de Barcelona estarán peor para moverse hoy y por qué?

Índice 0–100 por barrio·hora combinando tráfico, meteo, calidad del aire, accidentes históricos y POIs. Explicaciones en lenguaje natural vía Claude Haiku 4.5.

---

## Variables de entorno

Copia `.env.example` a `.env` y rellena los valores. **`.env` está en `.gitignore` — nunca se sube al repo.**

```powershell
Copy-Item .env.example .env
# Edita .env y pon ANTHROPIC_API_KEY=sk-ant-...
```

| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | Clave de Anthropic para Claude Haiku |
| `DEMO_OFFLINE` | `1` para servir solo del snapshot, sin llamar APIs externas |
| `CORS_ORIGINS` | Orígenes permitidos (en prod: URL de Vercel) |
| `VITE_API_BASE_URL` | URL del backend (en local: `http://localhost:8000`) |

---

## Arrancar la app en local

### Opción A — script todo-en-uno (Windows)

```powershell
.\start.ps1
```

Abre 2 ventanas de PowerShell (backend en `:8000`, frontend en `:3000`) y lanza el navegador. Necesitas Python 3.11 + Node 18+ instalados.

### Opción B — manual (2 terminales)

```powershell
# Terminal 1 — backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev      # http://localhost:3000
```

### Opción C — Docker Compose

```powershell
cd devops/infra
docker compose up --build
```

Backend: `http://localhost:8000` · Frontend: `http://localhost:3000`.

---

## Pipeline de datos (regenerar UFI)

Solo necesario si cambias modelos o quieres datos frescos.

```powershell
cd data-ml
pip install -e ".[dev]"
python -m data.ingest         # limpia hospitales, ingesta TRAMS/meteo/aire
python -m ml.train_trafico    # entrena LightGBM tráfico
python -m ml.train_accidentes # entrena LightGBM Poisson accidentes
python -m ml.score            # → data/processed/ufi_latest.parquet
```

El backend lee `data/processed/ufi_latest.parquet`. El Dockerfile raíz lo copia en la imagen para Railway.

---

## Modo demo offline

```powershell
$env:DEMO_OFFLINE=1
cd backend
uvicorn app.main:app --port 8000
```

Sirve del snapshot sin llamar a APIs externas ni a Claude.

---

## Estructura del repo

```
frontend/        React + Vite + MapLibre + deck.gl
backend/         FastAPI + DuckDB + Claude Haiku
data-ml/         pandas + LightGBM → ufi_latest.parquet
devops/          Docker Compose + Railway config + scripts demo
data/
  raw/           CSVs originales (read-only)
  processed/     Parquets y GeoJSONs generados por data-ml
  cache/         SQLite cache APIs externas
Dockerfile       Imagen Railway (backend + datos procesados)
start.ps1        Launcher local Windows
.env.example     Plantilla de variables (copiar a .env)
```

---

## Deploy (cloud)

### Frontend → Vercel

El proyecto ya está enlazado (`frontend/.vercel/project.json` local, no committeado).

**Recomendado: auto-deploy desde GitHub.** Conecta el repo en el dashboard de Vercel:
- Project Settings → Git → conectar a `llevadot11/prova1_claude`
- Root Directory: `frontend`
- Build: `npm run build` · Output: `dist`
- Env var: `VITE_API_BASE_URL` = URL pública de Railway

Una vez conectado, **cada push a `main` despliega automáticamente**. No hace falta correr nada local.

### Backend → Railway

Railway lee `Dockerfile` raíz + `devops/infra/railway.json`.

**Recomendado: auto-deploy desde GitHub.** En el dashboard de Railway:
- New Project → Deploy from GitHub repo → `llevadot11/prova1_claude`
- Variables → `ANTHROPIC_API_KEY`, `CORS_ORIGINS=https://<tu-vercel-url>`
- Settings → Generate Domain

Cada push a `main` redespliega.

### Datos en la imagen Railway

El `Dockerfile` raíz copia `data/processed/{barrios.geojson, tramos.geojson, mapping_barrios.csv, ufi_latest.parquet}` dentro de la imagen. Si regeneras el Parquet (`python -m ml.score`), tienes que **committear esos 4 archivos** y pushear para que Railway los incluya en el siguiente build.

---

## Endpoints principales

```
GET /barrios                     → GeoJSON 73 barrios
GET /ufi?at=<iso>&mode=default   → UFI por barrio·hora
GET /barrio/{id}?at=&mode=       → detalle con valores crudos
GET /explain/{id}?at=&mode=      → explicación en castellano (Claude)
GET /tramos/state?at=            → estado de tramos viarios
GET /modes                       → presets de pesos
GET /health                      → estado servicios upstream
GET /docs                        → Swagger UI
```

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite + TypeScript + MapLibre + deck.gl + Tailwind + Zustand |
| Backend | FastAPI + httpx + Pydantic v2 + DuckDB |
| ML / datos | pandas + geopandas + LightGBM + scikit-learn |
| Storage | DuckDB sobre Parquet + SQLite (cache) |
| LLM | Claude Haiku 4.5 (Anthropic) con prompt caching |
| Infra | docker-compose (local) · Vercel (frontend) · Railway (backend) |
