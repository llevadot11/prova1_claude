# Tareas — Persona B (Backend)

> Abre esta carpeta en Claude Code con `claude` desde `backend/`.
> Marca cada tarea con `[x]` al terminarla.

---

## Bloque 1 — Viernes 19:00–22:00 (Setup + stubs funcionales)

- [ ] **`pip install -e ".[dev]"`** y verifica que arranca sin errores
- [ ] **`uvicorn app.main:app --reload`** y comprueba que `http://localhost:8000/docs` carga
- [ ] **Ejecutar `pytest`** — los 7 tests smoke deben pasar (ya escritos, usan stubs)
- [ ] **Acordar contrato con A** (22:00 vie): revisar juntos `schemas.py` + `api.ts`, confirmar que todos los campos casan
- [ ] **Verificar hito H0**: que A puede hacer fetch a `/ufi` y recibe 73 barrios con schema correcto

---

## Bloque 2 — Sábado 09:00–14:00 (Integración Open-Meteo + Parquet real)

- [ ] **Wrapper Open-Meteo Forecast** en `app/meteo_client.py`:
  - Fetch async con httpx a `api.open-meteo.com/v1/forecast`
  - Parámetros: `latitude, longitude, hourly=temperature_2m,precipitation,wind_speed_10m,humidity`
  - Cache SQLite 30 min por `(lat, lon, fecha)`
- [ ] **Wrapper Open-Meteo AQ** en `app/aq_client.py`:
  - Fetch `air-quality-api.open-meteo.com` con `pm10,pm2_5,nitrogen_dioxide,ozone`
  - Cache SQLite 30 min
- [ ] **`store.py` — leer Parquet real** (cuando C lo entregue):
  - Reemplazar el stub de `load_ufi()` con lectura DuckDB:
    ```sql
    SELECT * FROM parquet WHERE timestamp = ? AND barrio_id IN (...)
    ```
  - Aplicar pesos del modo on-the-fly sobre las 5 columnas `score_*`
  - Normalizar si el rango es muy estrecho (clamp 0–100)
- [ ] **`store.py` — leer GeoJSONs** de `data/processed/barrios.geojson` y `tramos.geojson` (cuando C los entregue)

---

## Bloque 3 — Sábado 14:00–22:00 (Explain + robustez)

- [ ] **`explain.py` — verificar con Claude API real**:
  - Añade `ANTHROPIC_API_KEY` al `.env`
  - Prueba con `curl /explain/BAR-001` y verifica que llega una frase natural
  - Confirmar que el cache funciona: segunda llamada idéntica devuelve `"cached": true`
- [ ] **`health.py` — pings reales**:
  - Añadir ping a Anthropic (puede ser HEAD al models endpoint)
  - Logear latencias
- [ ] **Manejo de errores upstream**:
  - Si Open-Meteo cae → `store.py` sirve del Parquet sin el override de meteo fresco
  - Si Anthropic cae → `explain.py` devuelve la plantilla de fallback
  - Nunca devolver 500 desde `/ufi` o `/barrio`
- [ ] **CORS**: verificar que la URL pública de Railway acepta requests desde la URL de Vercel (A necesita esto)
- [ ] **Env var `RAILWAY_URL`** en `.env.example` para que A configure `VITE_API_BASE_URL`

---

## Bloque 4 — Domingo 09:00–14:00 (Pulido + performance)

- [ ] **Endpoint `/ufi` optimizado**: si el Parquet tiene 73×48=3.504 filas, la query debe ser < 50ms
- [ ] **Paginación del GeoJSON de tramos**: si pesa > 1MB, comprimir con gzip (FastAPI lo hace automático con `Content-Encoding: gzip`)
- [ ] **Logging estructurado** con hora UTC para depurar en demo
- [ ] **Revisar tests**: que todos pasen con el Parquet real de C

---

## Criterio de "done" para la demo

- [ ] `pytest` pasa (todos los tests)
- [ ] `/health` devuelve `"api": "ok"` + status de Open-Meteo y Anthropic
- [ ] `/ufi` responde en < 100ms
- [ ] `/explain` responde en < 3s (con Claude) y en < 50ms (con cache hit)
- [ ] `DEMO_OFFLINE=1` → app funciona sin red
- [ ] Sin claves en el código (D hace security-review antes del deploy)
