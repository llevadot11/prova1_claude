# Backend — Pendientes y propuestas

> Estado a 2026-05-07. Las secciones marcadas con ⚠️ bloquean la demo si no se resuelven.

---

## Pendientes confirmados (del plan original)

### ⚠️ Coordinación con A
- Revisar `schemas.py` vs `frontend/src/api.ts` y confirmar que todos los campos casan.
- Verificar H0 en vivo: que A hace fetch a `/ufi` y recibe 73 barrios con el schema correcto.

### ⚠️ Dependencia de C — datos reales
- `store.py` tiene la query DuckDB lista, pero necesita `data/processed/ufi_latest.parquet`.
- `load_barrios_geojson()` y `load_tramos_geojson()` leen de disco si existen — dependen de `barrios.geojson` y `tramos.geojson` de C.
- `load_tramos_state()` sigue siendo stub determinista. Necesita datos del CSV de tráfico procesados por C.

### ⚠️ Prueba de explain con API key real
- Crear `.env` en la raíz del repo con `ANTHROPIC_API_KEY=sk-...`
- `curl http://localhost:8000/explain/BAR-001` y verificar que llega una frase en castellano.
- Segunda llamada idéntica debe devolver `"cached": true`.

### `load_barrio_detail()` — raw values reales
- Actualmente genera `temperature_2m`, `precipitation_mm`, `pm2_5`, `no2` con `random.Random`.
- Pendiente: llamar a `meteo_client.get_forecast()` y `aq_client.get_air_quality()` con el centroide del barrio para devolver valores reales.
- Requiere que C entregue los centroides de barrios (lat/lon por `barrio_id`), o que se calculen del GeoJSON.

### `health.py` — ping real a Anthropic
- Ahora solo comprueba si hay `ANTHROPIC_API_KEY` configurada.
- Pendiente: HEAD a `https://api.anthropic.com` (o GET `/v1/models`) para verificar conectividad real.

### Benchmark de `/ufi` < 50ms
- No hay test de performance automatizado.
- Con el Parquet real de C, medir con `time curl /ufi` o pytest-benchmark.

---

## Propuestas a verificar

### P1 — Script de pre-warm del cache de explain
Para la demo del sábado por la noche, pre-calentar los 73 barrios × 1 hora × 4 modos = 292 llamadas a Claude.
Evita latencias de 3s durante la demo. D lo ejecutaría antes del congelado.

```python
# scripts/prewarm_explain.py (a crear)
# itera barrio_id, mode, llama GET /explain/{id}?mode=X
```

### P2 — Enriquecer `load_barrio_detail()` con Open-Meteo
Cuando C entregue los centroides, sustituir los `raw` aleatorios por valores reales de `meteo_client` y `aq_client`.
Impacto: las explicaciones de Claude serán más precisas (reciben temperatura y PM2.5 reales).

### P3 — Endpoint `GET /barrio/{id}/explain` con streaming
Si la latencia de Claude resulta molesta en demo, añadir `stream=True` y devolver `text/event-stream`.
El front puede ir mostrando la frase mientras se genera. Bajo impacto en A si se añade como endpoint nuevo.

### P4 — Cache de `/ufi` en memoria (TTL 5 min)
El Parquet no cambia entre llamadas dentro de la misma hora. Un `functools.lru_cache` con TTL evitaría releer DuckDB en cada request.
Implementación simple con `cachetools.TTLCache` (ya en el entorno por ser dep transitiva de anthropic).

### P5 — Ruta `/snapshot` para modo demo offline
En lugar de servir stubs aleatorios, cargar un JSON estático pre-generado de 73 barrios con datos reales.
D generaría el snapshot el sábado noche. Más fiel a la realidad que los stubs.

### P6 — Validación del schema del Parquet al arrancar
Al iniciar uvicorn, comprobar que el Parquet tiene las columnas esperadas (`score_trafico`, etc.).
Si falta alguna columna, loguear warning en vez de explotar en runtime con un KeyError.

```python
# app/store.py — añadir en startup
@app.on_event("startup")
def _validate_parquet_schema(): ...
```

### P7 — Tests de integración con Parquet de fixture
Crear `tests/fixtures/mini.parquet` con 5 barrios × 2 horas para que los tests de `load_ufi()` cubran la rama DuckDB real sin depender de C.

---

## No hacer (fuera de alcance para este hackathon)

- Autenticación / rate limiting (no hay usuarios externos).
- WebSockets para updates en tiempo real (slider temporal es suficiente).
- Cache distribuida (Redis): SQLite es suficiente para la demo.
- Paginación de `/barrios` o `/tramos`: 73 barrios y ~530 tramos caben en una sola respuesta.
