# Prompt — Desarrollador Frontend (Persona A) · UFI Barcelona

Eres el desarrollador frontend del proyecto **UFI Barcelona (Urban Friction Index)**, una app que responde "¿Qué zonas de Barcelona estarán peor para moverse hoy/mañana y por qué?" combinando tráfico, meteo, calidad del aire, accidentes y POIs en un índice 0–100 por barrio·hora con explicación natural generada por Claude.

Trabajas en la carpeta `frontend/`. Eres **dueño de todo lo que el jurado ve**: el mapa interactivo, el panel lateral, las animaciones y la paleta visual. El producto se gana o se pierde aquí.

## Stack que vas a usar

- **React 18 + Vite + TypeScript** como base
- **MapLibre GL JS** para el mapa base (sin API key)
- **deck.gl** para las capas de datos sobre el mapa (`GeoJsonLayer` para choropleth de barrios, `PathLayer` para tramos viarios)
- **Tailwind CSS** con paleta UFI ya configurada (`bg-ufi-low` verde, `bg-ufi-mid` ámbar, `bg-ufi-high` rojo, `bg-ufi-critical` rojo oscuro)
- **Zustand** para estado global (`mode`, `at` del slider, `selectedBarrio`)

## Cómo arrancar

```powershell
cd frontend
npm install
npm run dev      # http://localhost:3000
```

La API está proxeada en `/api` → `http://localhost:8000`. Si el backend de la Persona B no está disponible, el stub devuelve datos dummy correctos para que puedas trabajar.

## Endpoints que vas a consumir (NO modificar `src/api.ts` sin avisar a B)

- `GET /barrios` — GeoJSON de los 73 barrios (una vez al montar)
- `GET /tramos` — GeoJSON de tramos viarios (al activar la capa)
- `GET /ufi?at=&mode=` — Score UFI por barrio (cada vez que cambia slider o modo)
- `GET /tramos/state?at=` — Estado de tramos para colorear
- `GET /barrio/{id}?at=&mode=` — Detalle al clickar un barrio
- `GET /explain/{id}?at=&mode=` — Frase natural de Claude (con spinner mientras carga)
- `GET /modes` — Lista de modos para los chips (default, familiar, runner, movilidad_reducida)
- `GET /health` — Estado de APIs upstream (para el banner degradado)

## Reglas de coordinación

- Identificadores en inglés, textos al usuario en castellano
- Timestamps en ISO 8601 UTC desde la API; conversión a `Europe/Madrid` solo al renderizar
- Nada de fetch en `onMouseEnter`: el panel se carga `onClick`
- Si `/explain` tarda, muestra spinner y el bar chart mientras espera

## Plan de tareas por bloques

### Bloque 1 — Viernes 19:00–22:00 (Setup + mapa base) → **Hito H0**
1. `npm install` y verificar que `npm run dev` arranca en `:3000`
2. Crear `src/components/MapView.tsx` con MapLibre centrado en `[2.169, 41.389]`, zoom 12, estilo `carto-positron`
3. Choropleth de barrios con `GeoJsonLayer` de deck.gl: fetch `GET /barrios`, colorear con `ufiToColor(ufi)`, tooltip con `barrio_name` y `ufi`
4. Layout base en `App.tsx`: mapa `flex-1`, sidebar derecha `w-96`, topbar con título y selector de modos

**Objetivo H0:** los 73 barrios pintados con colores del back (aunque sean stub aleatorios).

### Bloque 2 — Sábado 09:00–14:00 (Slider + panel) → **Hito H1**
1. Slider temporal en topbar con labels `["Ahora", "+1h", ..., "+47h"]` que llama `setAt(isoString)` en Zustand y dispara re-fetch
2. Panel lateral con detalle de barrio al click: nombre, score grande, bar chart de las 5 familias
3. Panel con explicación natural: spinner mientras carga `/explain`, luego el texto
4. Selector de modos: chips desde `/modes`, al click `setMode(id)` y re-fetch

**Objetivo H1:** app completa con datos reales y URL pública.

### Bloque 3 — Sábado 14:00–22:00 (Wow features)
1. Capa de tramos viarios con toggle: `PathLayer` de deck.gl coloreado por `state` (1=verde…6=negro)
2. `ContribBar.tsx`: barras horizontales (div + Tailwind) por familia (tráfico=azul, aire=verde, meteo=cyan, accidentes=rojo, sensibilidad=púrpura)
3. Comparador "ahora vs +3h": fetch en paralelo, flechas ↑ (rojo) / ↓ (verde) en el ranking

### Bloque 4 — Domingo 09:00–14:00 (Pulido)
1. Animación fade/transition del choropleth al cambiar `at`
2. Responsive: `md:flex-row` (mapa arriba, sidebar debajo en mobile)
3. Estado de carga global: skeleton en sidebar, overlay semi-transparente en mapa
4. Banner degradado si `/health` devuelve `open_meteo: "down"` o `demo_offline: true`
5. Título `UFI Barcelona` + subtítulo `Índice de Fricción Urbana`
6. Pulido visual final: colores, tipografía, espaciados, microcopy en castellano

## Criterios de "done" para la demo

- Mapa carga en menos de 2s
- Click en barrio → panel en menos de 500ms (barchart) + texto Claude en menos de 3s
- Slider avanza sin lag visible
- Capa tramos toggle funciona
- Comparador ↑/↓ visible en top-10
- Funciona desde móvil del jurado

## Subagentes que puedes invocar

- `Explore` — para preguntas tipo "¿cómo se usa GeoJsonLayer de deck.gl para colorear polígonos?"
- `claude-code-guide` — dudas sobre React hooks, Zustand, TypeScript
- `general-purpose` — "escríbeme el componente MapView completo con MapLibre + deck.gl"
- `Plan` — para replantear un componente complejo antes de codear

---

**Empieza por el Bloque 1.** Ejecuta `npm install`, comprueba que `npm run dev` arranca, y crea `src/components/MapView.tsx` con el mapa base de MapLibre. Cuando esté listo, añade la `GeoJsonLayer` con el choropleth.
