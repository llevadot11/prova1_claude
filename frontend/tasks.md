# Tareas — Persona A (Frontend)

> Abre esta carpeta en Claude Code con `claude` desde `frontend/`.
> Marca cada tarea con `[x]` al terminarla.

---

## Bloque 1 — Viernes 19:00–22:00 (Setup + mapa base)

- [x] **`npm install`** y verifica que `npm run dev` arranca en `:3000`
- [x] **Mapa MapLibre base** en `src/components/MapView.tsx`:
  - Renderiza mapa de Barcelona centrado en `[2.169, 41.389]`, zoom 12
  - Sin capas todavía, solo el tile base (MapLibre + estilo libre como `carto-positron`)
- [x] **Choropleth de barrios** (`GeoJsonLayer` de deck.gl):
  - Fetch `GET /barrios` al montar
  - Colorea cada polígono con la función `ufiToColor(ufi)` que mapea 0–100 a la paleta UFI
  - Tooltip básico con `barrio_name` y `ufi`
- [x] **Layout base** en `App.tsx`:
  - Mapa ocupa `flex-1`
  - Sidebar derecha `w-96`
  - Topbar con título y selector de modos

**Hito H0 (22:00 vie)**: mapa con 73 barrios coloreados con datos del back (aunque sean stub aleatorios).

---

## Bloque 2 — Sábado 09:00–14:00 (Slider + panel)

- [x] **Topbar — Slider temporal**:
  - Genera array de labels `["Ahora", "+1h", "+2h", ... "+47h"]`
  - Al mover, llama `setAt(isoString)` en Zustand
  - El mapa re-fetcha `/ufi?at=<iso>` y se re-colorea
- [x] **Panel lateral — detalle de barrio**:
  - Al click en polígono → `selectBarrio(barrio_id)` en Zustand
  - Fetch `GET /barrio/{id}?at=&mode=`
  - Muestra: nombre, score grande, bar chart de 5 familias
- [x] **Panel lateral — explicación natural**:
  - Fetch `GET /explain/{id}?at=&mode=`
  - Muestra spinner mientras carga, luego el texto
- [x] **Selector de modos**:
  - Fetch `GET /modes` al montar, pinta chips
  - Al click → `setMode(id)`, re-fetcha el mapa

**Hito H1 (14:00 sáb)**: app completa con datos reales y URL pública de D.

---

## Bloque 3 — Sábado 14:00–22:00 (Wow features)

- [x] **Capa tramos viarios** (toggle):
  - Fetch `GET /tramos` (GeoJSON de líneas)
  - Fetch `GET /tramos/state?at=` para colorear
  - `PathLayer` de deck.gl, coloreado por `state` (1=verde…6=negro)
  - Checkbox toggle en topbar
- [x] **Bar chart de contribuciones** como componente propio `ContribBar.tsx`:
  - Barras horizontales (div + Tailwind) para cada familia
  - Colores por familia: tráfico=azul, aire=verde, meteo=cyan, accidentes=rojo, sensibilidad=púrpura
- [x] **Comparador "ahora vs +3h"**:
  - Fetch UFI actual y UFI+3h en paralelo
  - En cada barrio del ranking → flecha ↑ (rojo) o ↓ (verde) según dirección del cambio

---

## Bloque 4 — Domingo 09:00–14:00 (Pulido)

- [x] **Animación del choropleth** al cambiar `at` (fade/transition suave)
- [x] **Responsive**: mapa arriba, sidebar debajo en mobile (`md:flex-row`)
- [x] **Estado de carga global**: skeleton en sidebar, overlay semi-transparente en mapa
- [x] **Banner degradado** si `/health` devuelve `open_meteo: "down"` o `demo_offline: true`
- [x] **Título bonito** en topbar: `UFI Barcelona` + subtítulo `Índice de Fricción Urbana`
- [x] **Pulido visual final**: revisar colores, tipografía, espaciados, microcopy en castellano

---

## Criterio de "done" para la demo

- [x] Mapa carga en < 2s en primera visita
- [x] Click en barrio → panel aparece en < 500ms (barchart) + texto Claude en < 3s
- [x] Slider avanza sin lag visible
- [x] Capa tramos toggle funciona
- [x] Comparador ↑/↓ visible en top-10
- [x] Funciona desde móvil del jurado
