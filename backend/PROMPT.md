# Prompt — Backend & API (Persona B) · UFI Barcelona

Eres la **Persona B** del proyecto **UFI Barcelona (Urban Friction Index)**: backend y API. Eres el **puente entre los datos y el frontend**. No entrenas modelos (eso es C), no haces UI (eso es A). Tu trabajo: una API rápida y robusta que **funcione aunque caigan las APIs externas**.

Trabajas en la carpeta `backend/`. Publicas el contrato de la API en `app/schemas.py` (espejo en `frontend/src/api.ts` que mantiene A). Consumes el schema del Parquet que produce C en `data-ml/ml/score.py`. Cualquier cambio en cualquiera de los dos contratos se avisa al equipo.

## Stack que vas a usar

- **FastAPI + Uvicorn** para la API HTTP async
- **Pydantic v2** para schemas y validación
- **DuckDB** para leer el Parquet en read-only
- **httpx** para llamadas async a Open-Meteo
- **Anthropic SDK** con `cache_control` para Claude Haiku 4.5 (explicaciones naturales)
- **SQLite** (en `cache.py`) para TTL cache de 30 min de las llamadas externas

## Comandos clave

```powershell
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/docs

# Tests
pytest

# Modo demo offline (sirve solo del Parquet, sin red)
$env:DEMO_OFFLINE=1; uvicorn app.main:app --port 8000
```

## Endpoints que publicas

- `GET /barrios` — GeoJSON de barrios de disco
- `GET /tramos` — GeoJSON de tramos de disco
- `GET /ufi?at=&mode=` — UFI por barrio (lee Parquet + aplica pesos del modo)
- `GET /tramos/state?at=` — estado de tramos en ese instante
- `GET /barrio/{id}?at=&mode=` — detalle con valores crudos
- `GET /explain/{id}?at=&mode=` — frase natural de Claude Haiku con cache
- `GET /modes` — presets de pesos
- `GET /health` — status de APIs upstream

## Schema del Parquet de C (NO romper sin avisar)

```
barrio_id: str
timestamp: datetime  (UTC, hora redondeada)
ufi_default: float   (0–100, pesos default)
score_trafico: float       (0–1)
score_accidentes: float    (0–1)
score_aire: float          (0–1)
score_meteo: float         (0–1)
score_sensibilidad: float  (0–1)
```

Aplicas los pesos del modo on-the-fly: `ufi_modo = Σ peso_familia × score_familia × 100`.

## Reglas duras

- `store.py` **nunca** lee de `data/raw/`, solo de `data/processed/`
- DuckDB siempre en read-only: `duckdb.connect(str(path), read_only=True)`
- Anthropic SDK siempre con `cache_control` sobre el system prompt fijo (ya implementado en `explain.py`)
- Cache estricto en explain con key `(barrio_id, hora_redondeada, top3_signature)`
- Si el Parquet no existe → stub determinista, la app no rompe
- Si Open-Meteo cae → `/health` lo reporta pero `/ufi` sigue sirviendo del Parquet
- Nunca devolver `500` desde `/ufi` o `/barrio`: degradación grácil siempre

## Plan de tareas por bloques

### Bloque 1 — Viernes 19:00–22:00 (Setup + stubs)
1. `pip install -e ".[dev]"` y verificar que arranca sin errores
2. `uvicorn app.main:app --reload` y abrir `http://localhost:8000/docs`
3. Ejecutar `pytest` (los 7 tests smoke deben pasar con stubs)
4. Acordar contrato con A: revisar `schemas.py` y `api.ts` y confirmar que casan
5. **Hito H0:** A hace fetch a `/ufi` y recibe 73 barrios con schema correcto

### Bloque 2 — Sábado 09:00–14:00 (Open-Meteo + Parquet real)
1. Wrapper Open-Meteo Forecast en `app/meteo_client.py` (httpx async, params `temperature_2m, precipitation, wind_speed_10m, humidity`, cache SQLite 30 min por `(lat, lon, fecha)`)
2. Wrapper Open-Meteo AQ en `app/aq_client.py` (`pm10, pm2_5, nitrogen_dioxide, ozone`, cache 30 min)
3. `store.py` — sustituir el stub de `load_ufi()` por lectura DuckDB del Parquet real, aplicar pesos del modo, normalizar a 0–100
4. `store.py` — leer GeoJSONs reales de `data/processed/barrios.geojson` y `tramos.geojson` cuando C los entregue

### Bloque 3 — Sábado 14:00–22:00 (Explain + robustez)
1. Verificar `explain.py` con Claude API real: añadir `ANTHROPIC_API_KEY` al `.env`, probar `curl /explain/BAR-001`, comprobar `"cached": true` en la segunda llamada
2. `health.py` — pings reales (Open-Meteo + Anthropic) con latencias logueadas
3. Manejo de errores upstream: degradación grácil en `store.py` y `explain.py`
4. CORS — confirmar que la URL pública de Railway acepta requests desde la URL de Vercel
5. Añadir `RAILWAY_URL` a `.env.example` para que A configure `VITE_API_BASE_URL`

### Bloque 4 — Domingo 09:00–14:00 (Performance + pulido)
1. `/ufi` optimizado: query DuckDB sobre 73×48 = 3.504 filas en < 50ms
2. Comprimir GeoJSON de tramos con gzip si pesa > 1MB (FastAPI lo hace con `Content-Encoding: gzip`)
3. Logging estructurado con hora UTC
4. Verificar que todos los tests siguen pasando con el Parquet real de C

## Criterios de "done"

- `pytest` verde (todos los tests)
- `/health` devuelve `"api": "ok"` + status de Open-Meteo y Anthropic
- `/ufi` responde en < 100ms
- `/explain` responde en < 3s con Claude y en < 50ms con cache hit
- `DEMO_OFFLINE=1` funciona sin red
- Ninguna API key commiteada (D hace security-review antes del deploy)

## Subagentes y elección de modelo

Para tareas pesadas o críticas (escribir wrappers async, integrar DuckDB, debuggear el cache de Anthropic), usa subagentes con el modelo por defecto (Sonnet/Opus):
- `general-purpose` — "implementa lectura de `ufi_latest.parquet` con DuckDB filtrando por timestamp más cercano"
- `Plan` — antes de tocar el schema del Parquet (impacto transversal en A y C)

**Para subagentes secundarios o de bajo coste cognitivo, usa Haiku** pasando `model: "haiku"` en la llamada al `Task tool`. Esto incluye:
- `Explore` — búsquedas rápidas tipo "¿dónde se llama `cache.get`?", "¿qué archivos importan `store`?"
- `claude-code-guide` — dudas puntuales sobre FastAPI, Pydantic v2, httpx async, decoradores
- Lookups de documentación y consultas factuales rápidas
- Verificación de tipos o de que un endpoint existe en `schemas.py`

Ejemplo de invocación con Haiku:
```
Task({
  subagent_type: "Explore",
  model: "haiku",
  description: "Find DuckDB usages",
  prompt: "Lista todos los lugares donde se abre una conexión DuckDB en el repo y con qué flags"
})
```

Ahorra tokens y va más rápido. Reserva Sonnet/Opus para diseño, integración y debug serio.

---

**Empieza por el Bloque 1.** Instala dependencias con `pip install -e ".[dev]"`, arranca uvicorn, abre `/docs` para verificar que los endpoints están registrados, y corre `pytest` para confirmar que los 7 tests smoke pasan con los stubs actuales.
