# Persona B — Backend & API

**Tu carpeta**: `backend/`
**Contrato que publicas**: [app/schemas.py](app/schemas.py) — espejo en `frontend/src/api.ts`. Cualquier cambio → avisa a A.
**Contrato que consumes**: [data-ml/ml/score.py](../data-ml/ml/score.py) define el schema del Parquet. Cualquier cambio → te avisa C.

---

## Tu rol en el equipo

Eres el puente entre los datos y el front. No entrenas modelos (eso es C). No haces UI (eso es A). Tu trabajo: API rápida y robusta que funcione aunque caigan las APIs externas.

---

## Stack

| Herramienta | Para qué |
|---|---|
| FastAPI + Uvicorn | API HTTP async |
| Pydantic v2 | Schemas + validación |
| DuckDB | Lee Parquet en modo read-only |
| httpx | Llamadas a Open-Meteo |
| Anthropic SDK | Llama a Claude Haiku 4.5 para explicaciones |
| SQLite (cache.py) | TTL cache de llamadas externas |

---

## Comandos

```powershell
# Desde la carpeta backend/
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Tests smoke (requieren solo TestClient, sin red)
pytest

# Modo demo offline
$env:DEMO_OFFLINE=1; uvicorn app.main:app --port 8000
```

---

## Estructura de ficheros

```
backend/
  app/
    main.py        Routing + CORS. NO añadir lógica aquí.
    schemas.py    Contrato Pydantic → espejo en frontend/src/api.ts.
    config.py     Settings (pydantic-settings + .env raíz).
    modes.py      Pesos de los 4 modos. C define, tú publicas.
    store.py      Lee data/processed/ufi_latest.parquet.
                  STUB determinista hasta que C entregue el Parquet real.
    cache.py     SQLite TTL 30 min.
    explain.py    Claude Haiku 4.5 + cache estricto + fallback plantilla.
    health.py    Pings a APIs upstream.
  tests/
    test_smoke.py  7 tests contra TestClient.
  tasks.md        ← TU LISTA DE TAREAS
  skills.md       ← Subagentes y skills útiles
```

---

## Endpoints que publicas

| Método | Ruta | Responsable |
|---|---|---|
| GET | `/barrios` | Lee GeoJSON de disco |
| GET | `/tramos` | Lee GeoJSON de disco |
| GET | `/ufi?at=&mode=` | Lee Parquet + aplica pesos |
| GET | `/tramos/state?at=` | Lee Parquet o stub |
| GET | `/barrio/{id}?at=&mode=` | Detalle con raw values |
| GET | `/explain/{id}?at=&mode=` | Claude Haiku + cache |
| GET | `/modes` | Lista presets de pesos |
| GET | `/health` | Status APIs upstream |

---

## Schema del Parquet que C produce (NO romper)

```
barrio_id: str
timestamp: datetime  (UTC, hora redondeada)
ufi_default: float   (0-100, calculado con pesos default)
score_trafico: float (0-1)
score_accidentes: float (0-1)
score_aire: float (0-1)
score_meteo: float (0-1)
score_sensibilidad: float (0-1)
```

Tú aplicas los pesos del modo on-the-fly: `ufi_modo = Σ peso_familia × score_familia × 100`.

---

## Reglas duras

- **`store.py` NUNCA lee `data/raw/`**: solo `data/processed/`.
- **DuckDB en read-only**: `duckdb.connect(str(path), read_only=True)`.
- **Anthropic SDK con `cache_control`** sobre el system prompt (ya implementado en `explain.py`).
- **Cache estricto en explain**: key `(barrio_id, hora_redondeada, top3_signature)`.
- Si el Parquet no existe todavía → `store.py` devuelve stub determinista. No rompe la app.
- Si Open-Meteo cae → `/health` lo reporta, pero `/ufi` sigue sirviendo del Parquet.

---

## Subagents que puedes pedir a Claude Code

Ver [skills.md](skills.md). Resumen:
- `general-purpose` → *"Implementa la lectura de ufi_latest.parquet con DuckDB filtrando por timestamp más cercano"*
- `Explore` → *"¿Cómo funciona el prompt caching de Anthropic en streaming?"*
- `claude-code-guide` → dudas sobre FastAPI, Pydantic v2, httpx async
- `Plan` → antes de cambiar el schema del Parquet (impacto transversal)
