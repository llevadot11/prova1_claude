# FUTURE.md — UFI Barcelona · Roadmap Frontend

## Mejoras inmediatas (antes o justo después de la demo)

### Bugs conocidos
- **ContribBar barra invisible**: si `contribution_pct < 2`, la barra queda invisible. Añadir `min-width: 4px` con `style={{ minWidth: "4px" }}`.
- **Banner degradado sin cierre**: el banner de demostración no se puede descartar. Añadir botón `×` con `setDegraded(false)`.
- **Error silencioso en BarrioPanel**: si `/barrio/{id}` falla, el panel muestra nada sin aviso. Añadir estado `error` y mensaje visible al usuario.
- **comp3h stale**: las flechas ↑↓ siguen mostrando el comparador anterior mientras carga el nuevo. Resetear `setComp3h({})` al inicio del efecto.

### Accesibilidad rápida
- `<li>` del top-10 actúa como botón pero no tiene `role="button"` ni `tabIndex={0}` ni `onKeyDown`. El jurado en móvil no notará, pero es deuda real.
- Contraste del texto `text-slate-400` sobre fondo blanco no supera WCAG AA. Subir a `text-slate-500`.
- El tooltip de deck.gl es un string plano sin estilos accesibles — irrelevante para la demo pero notable.

---

## Mid-term (semana post-hackathon)

### Rendimiento
- **Code splitting**: `maplibre-gl` (802 KB) y `deck.gl` (888 KB) deberían cargarse con `React.lazy` + `Suspense`. El tiempo de primera carga baja de ~3s a ~1s en conexión lenta.
- **Memoización de capas deck.gl**: `new GeoJsonLayer(...)` se recrea en cada render aunque los datos no cambien. Mover la construcción del array `layers` dentro de un `useMemo` con los deps correctos.
- **Debounce del slider**: mover el slider rápido dispara un fetch por cada posición. Añadir `debounce(setAt, 150ms)` para que solo fetchee cuando el usuario para.
- **Cache de GeoJSON**: el GeoJSON de barrios (73 polígonos) se re-parsea en cada render de `GeoJsonLayer`. Memoizar con `useMemo`.

### Arquitectura
- **Extraer lógica de fetch a custom hooks**: `useUFIData`, `useBarrioDetail`, `useComparator`. App.tsx tiene demasiadas responsabilidades mezcladas (~150 líneas de estado + efectos + render).
- **Unificar `ufiToColor` / `ufiChipClass` / `ufiTextClass`**: la misma lógica de colorización UFI está duplicada en `MapView.tsx`, `App.tsx` y `BarrioPanel.tsx`. Extraer a `src/utils/ufiColor.ts`.
- **Tipado de GeoJSON properties**: las propiedades `barrio_id`, `tram_id` se acceden como `f.properties?.barrio_id as string`. Crear tipos `BarrioFeature` y `TramFeature` extendiendo `Feature<Polygon, {barrio_id: string}>` para eliminar los `as` casts.

### UX
- **Leyenda del mapa**: rectángulos de color con etiquetas "Fluido / Moderado / Alto / Crítico". Sin esto el jurado no sabe qué significan los colores.
- **Timestamp visible**: mostrar la hora formateada (`Europe/Madrid`) del `at` seleccionado debajo del slider ("Predicción para: mié 7 may 15:00").
- **Deseleccionar barrio con click fuera del mapa**: actualmente solo se deselecciona desde el top-10. Añadir `onClick` en el fondo del mapa cuando no hay feature bajo el cursor.
- **Persistencia de estado en URL**: guardar `mode`, `at` e `id` de barrio seleccionado en query params. Permite compartir vistas (`?mode=familiar&barrio=gracia`).

---

## Long-term (siguientes versiones)

### Features no implementadas en la demo
- **Modo oscuro**: paleta `dark:` Tailwind. El mapa base tiene variante `dark-matter` de CARTO.
- **Animación temporal automática**: botón "play" que avanza el slider +1h cada segundo mostrando la evolución de la fricción.
- **Heatmap layer**: alternar entre choropleth de barrios y heatmap continuo con `HeatmapLayer` de deck.gl para una visualización más fluida.
- **Vista 3D extrudida**: `ColumnLayer` de deck.gl donde la altura del cilindro es el UFI. Espectacular para la demo con `pitch: 45`.
- **Mini-gráfico temporal por barrio**: sparkline 0-47h del UFI del barrio seleccionado. Requiere llamadas a `/ufi` para cada hora o un endpoint nuevo `/barrio/{id}/timeline`.
- **Comparador lado a lado**: dos mapas sincronizados con `t1` y `t2` para comparar visualmente.
- **Geocodificador**: buscador de dirección que centra el mapa y selecciona el barrio. MapLibre tiene soporte nativo.

### Capas de visualización nuevas
- **Capa POIs**: cafeterías, hospitales, escuelas de `data/hospitales.csv` como puntos `ScatterplotLayer`.
- **Capa accidentes históricos**: puntos de calor con `HeatmapLayer` sobre las coordenadas de accidentes.
- **Capa meteorológica**: iconos de lluvia/viento/temperatura superpuestos por zona.
- **Flujo de tráfico animado**: `TripsLayer` de deck.gl con trayectorias animadas sobre los tramos viarios.

### Tests
- Tests unitarios de `ufiToColor`, `ufiChipClass`, `indexToIso` con Vitest (están ya en package.json, 0% cobertura actual).
- Tests de integración de `BarrioPanel` con `msw` (Mock Service Worker) para simular respuestas de `/barrio` y `/explain`.
- Test E2E con Playwright: carga inicial, click en barrio, aparición del texto de Claude, slider funciona.

### Deuda técnica
- Eliminar el archivo `src/App.js` (JS plano) que aparece en el repo — probablemente un artefacto del scaffolding.
- Configurar ESLint con `eslint-plugin-react-hooks` para detectar deps de efectos erróneas.
- Añadir `prettier` para formateo consistente.
- Configurar `husky` + `lint-staged` para que el build no rompa en main.
- Revisar las vulnerabilidades moderadas de `npm audit` (5 detectadas en install).
