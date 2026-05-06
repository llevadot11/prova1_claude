# apps/api — UFI Backend

FastAPI + Pydantic + DuckDB. Lee `data/processed/ufi_latest.parquet` (lo produce `packages.ml.score`). NO entrena modelos: solo sirve.

## Layout

```
app/
  main.py        Router. NO añadir lógica aquí, solo routing.
  schemas.py    Contrato Pydantic (espejo en apps/web/src/api.ts).
  config.py     Settings via pydantic-settings + .env.
  modes.py      Pesos de los 4 modos (default/familiar/runner/movilidad_reducida).
  store.py      I/O DuckDB + Parquet + GeoJSON. Stub determinista si no hay ficheros.
  cache.py     SQLite TTL cache para Open-Meteo y Anthropic.
  explain.py    Wrapper Claude Haiku 4.5 + cache estricto + fallback plantilla.
  health.py    Status APIs upstream para banner del front.
tests/          pytest, smoke contra TestClient (los stubs).
```

## Comandos

```powershell
# Setup
cd apps/api; pip install -e ".[dev]"

# Run
uvicorn app.main:app --reload --port 8000

# Tests
pytest

# Demo offline
$env:DEMO_OFFLINE=1; uvicorn app.main:app --port 8000
```

## Reglas duras

- **No romper el contrato** sin avisar a A. Cambios en `schemas.py` → cambios en `apps/web/src/api.ts`.
- **No leer `data/raw/`** desde el API. Solo `data/processed/`.
- **Anthropic SDK SIEMPRE con `cache_control`** en el system prompt.
- **Cache estricto** en `explain.py` por `(barrio_id, hora_redondeada, top3_signature)`.
- **Errores upstream** no rompen `/ufi`: si el Parquet está, se sirve. El banner de health avisa.
- Pesos de los modos viven en `modes.py`. C define, B publica.

## Endpoints (cerrar viernes 19:00)

| Método | Ruta | Notas |
|---|---|---|
| GET | `/barrios` | GeoJSON 73 barrios |
| GET | `/tramos` | GeoJSON tramos viarios |
| GET | `/ufi?at=&mode=` | UFI por barrio |
| GET | `/tramos/state?at=` | Estado predicho por tramo |
| GET | `/barrio/{id}?at=&mode=` | Detalle con `raw` |
| GET | `/explain/{id}?at=&mode=` | Frase natural cacheada |
| GET | `/modes` | Presets de pesos |
| GET | `/health` | Status APIs upstream |

## Stub vs real

`store.py` devuelve **datos deterministas aleatorios** si no encuentra los ficheros — esto permite a A trabajar antes de que C entregue. Marcado con `TODO C`.
