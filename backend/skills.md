# Skills & Subagents — Persona B (Backend)

> Cómo sacarle el máximo partido a Claude Code desde tu carpeta.
> Abre Claude Code con `claude` desde `backend/`.

---

## Subagentes que puedes lanzar

### `general-purpose` — implementar funcionalidad compleja
**Úsalo cuando**: necesitas implementar un módulo completo o integrar una librería nueva.
```
Ejemplos:
"Implementa app/meteo_client.py. Requisitos:
 - httpx async
 - Fetch a api.open-meteo.com para una lista de (lat, lon) en paralelo con asyncio.gather
 - Cache SQLite TTL 30 min usando app/cache.py que ya existe
 - Devuelve Dict[barrio_id, Dict[hora_iso, Dict[variable, float]]]"

"Implementa la lectura real de ufi_latest.parquet en store.py load_ufi().
 Usa DuckDB en modo read_only=True.
 Query: seleccionar la hora más cercana a `at` para todos los barrios.
 Aplicar pesos del modo on-the-fly sobre las columnas score_*."

"Escribe el endpoint GET /tramos/state que devuelve la predicción de
 estatActual por tramo para la hora más cercana a `at`,
 leyendo de data/processed/trafico_pred.parquet"
```

### `Explore` — entender la codebase o una librería
```
"¿Cómo se hace una query de 'nearest timestamp' en DuckDB sobre un Parquet?"
"¿Qué opciones de cache_control soporta el Anthropic SDK para prompt caching?"
"¿Cómo configuro CORS en FastAPI para aceptar solo la URL de Vercel?"
"Busca dónde se usan los schemas Pydantic en main.py"
```

### `claude-code-guide` — dudas sobre el stack
```
"¿Cuál es la diferencia entre background_tasks y lifespan en FastAPI?"
"¿Cómo testeo un endpoint FastAPI async con pytest?"
"¿Cómo funciona el modelo de Settings de pydantic-settings con .env?"
```

### `Plan` — antes de cambios de arquitectura
```
Úsalo SIEMPRE antes de cambiar schemas.py o el schema del Parquet.
Impacto transversal: afecta a A (api.ts) y a C (score.py).

"Quiero añadir el campo `eventos` al BarrioDetail (eventos del día en ese barrio).
 ¿Cómo lo hago sin romper el contrato con A? ¿Dónde vive este dato?"
```

### `security-review` skill
Invoca con `/security-review` antes del deploy final. Verifica:
- Sin `ANTHROPIC_API_KEY` hardcodeada
- CORS no acepta `*` en producción
- Sin logging de valores sensibles

---

## Slash commands útiles

| Comando | Cuándo usarlo |
|---|---|
| `/review` | Cuando terminas un módulo. Antes de avisar a A o C. |
| `/simplify` | Si un endpoint tiene demasiada lógica interna. |
| `/security-review` | Antes de hacer deploy en Railway. |

---

## Patrones de prompt que funcionan bien

### Para implementar un endpoint
```
"Implementa el endpoint GET /barrio/{barrio_id} en main.py.
 - Llama a store.load_barrio_detail(barrio_id, at, mode)
 - Si devuelve None → HTTPException 404
 - El tipo de retorno es BarrioDetail (ya en schemas.py)
 - La función store.load_barrio_detail ya existe como stub: solo reemplaza
   la parte que calcula raw values con datos reales del Parquet"
```

### Para debug de un test que falla
```
"test_barrio_detail_ok falla con KeyError 'score_trafico'.
 El Parquet real de C tiene ese campo pero el stub de store.py no.
 Aquí está el traceback: [pega] y el stub actual: [pega]"
```

### Para optimización de query DuckDB
```
"La query de load_ufi tarda 800ms. El Parquet tiene 73×48=3504 filas.
 Aquí está la query actual: [pega].
 ¿Cómo la optimizo? ¿Debo añadir un índice o particionar el Parquet?"
```

---

## Reglas para no perder tiempo

1. **No cambiar `schemas.py` sin avisar a A**. Es el contrato más importante.
2. **Los tests smoke ya están escritos**. Si no pasan, algo está mal en el contrato.
3. **`store.py` tiene el stub**: trabaja sobre él, no lo reescribas desde cero.
4. **`explain.py` ya tiene la integración Claude**: solo verifica que el API key está y funciona.
