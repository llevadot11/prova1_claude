# Skills & Subagents — Persona C (Datos & ML)

> Cómo sacarle el máximo partido a Claude Code desde tu carpeta.
> Abre Claude Code con `claude` desde `data-ml/`.

---

## Subagentes que puedes lanzar

### `general-purpose` — escribir pipelines complejos
**Es tu subagente más valioso**. Úsalo para feature engineering, entrenamiento, ingesta.
```
Ejemplos:

"Escribe ml/features_trafico.py. Lee data/processed/trafico.parquet
 (columnas: idTram, timestamp, estatActual, estatPrevist).
 Genera para cada fila: lags estatActual 1h, 24h, 168h por idTram.
 Features temporales: hour, dow, month, is_holiday (python-holidays ca_ES),
 is_rush_hour (7-9 y 17-20 entre semana).
 Join con data/processed/meteo_single.parquet por hora más cercana.
 Output: DataFrame listo para LightGBM."

"Implementa data/ingest_73points.py.
 Lee data/processed/barrios.geojson, extrae lat/lon centroide de cada barrio.
 Para cada punto, hace fetch async a Open-Meteo hourly con los 4 campos.
 Usa asyncio + httpx con semaphore de 5 conexiones simultáneas.
 Output: data/processed/meteo_73pts.parquet con columnas barrio_id, time, temp, precip, wind, humid."

"Escribe el sjoin geopandas para mapear idTram → barrio_id.
 Input: data/processed/tramos.geojson (LineStrings) + data/processed/barrios.geojson (Polygons).
 Calcula el centroide de cada tramo con geopandas y hace sjoin con los polígonos de barrio.
 Output: data/processed/tramo_barrio.parquet con columnas idTram, barrio_id, barrio_name."
```

### `Explore` — entender los datos antes de codear
```
"¿Qué formato tiene el campo `data` en el CSV de TRAMS y cómo lo parseo con pandas?"
"¿Qué campos tiene el GeoJSON de barrios de Open Data BCN?"
"¿Cuáles son los parámetros de LightGBM para objective='poisson' en datasets pequeños?"
"¿Cómo se hace un spatial join en geopandas entre puntos y polígonos?"
```

### `claude-code-guide` — dudas de Python/ML
```
"¿Cómo genero lags de una serie temporal por grupo con pandas sin loop?"
"¿Cuál es la mejor forma de hacer split temporal con sklearn?"
"¿Cómo normalizo features 0-1 con clip en percentiles 5-95 para robustez?"
"¿Cómo serializo y cargo un modelo LightGBM con joblib?"
```

### `Plan` — antes de cambiar el schema del Parquet
```
CRÍTICO: el schema de salida de ml/score.py lo lee B en backend/app/store.py.
Antes de añadir/renombrar columnas, pide un plan:

"Quiero añadir score_eventos: float (0-1) al Parquet de UFI.
 ¿Cómo lo hago sin romper a B? ¿Qué orden de pasos seguir?"
```

---

## Slash commands útiles

| Comando | Cuándo usarlo |
|---|---|
| `/review` | Antes de decirle a B que el Parquet está listo. |
| `/simplify` | Si un pipeline tiene demasiados pasos intermedios. |

---

## Patrones de prompt que funcionan bien

### Para explorar un CSV nuevo
```
"Carga data/processed/accidentes.parquet con pandas y muéstrame:
 - shape
 - value_counts del campo de distrito
 - distribución horaria de accidentes
 - rango de años disponibles"
```

### Para debug del modelo
```
"El LightGBM Poisson da predicciones negativas en algunos tramos.
 ¿Por qué puede pasar con objective='poisson'? ¿Cómo lo corrijo?
 Aquí están las primeras filas del feature matrix: [pega]"
```

### Para el pipeline de scoring
```
"Reemplaza la función heuristic_scores() en ml/score.py con la versión real.
 Tienes disponibles:
 - data/processed/trafico_pred.parquet: columnas idTram, timestamp, estat_pred
 - data/processed/meteo_73pts.parquet: barrio_id, time, temp, precip, wind, humid
 - data/processed/aire_73pts.parquet: barrio_id, time, pm10, pm25, no2, o3
 - data/processed/accidentes_pred.parquet: barrio_id, hour, dow, riesgo_acc
 - data/processed/tramo_barrio.parquet: idTram, barrio_id
 
 El output debe mantener exactamente el schema fijo del docstring de score.py."
```

---

## Reglas para no perder tiempo

1. **Empieza por el GeoJSON de barrios y el mapping tramo→barrio**. Sin esto, nada funciona.
2. **El stub de score.py ya corre** — úsalo para verificar que B lee bien antes de tener el modelo real.
3. **Avisa a B cuando el Parquet real esté**: solo un mensaje en el chat del equipo.
4. **Split temporal SIEMPRE**: nunca aleatorio. Los tests de B lo detectarán si no.
5. **No rompas el schema del Parquet** sin Plan previo y aviso a B.
