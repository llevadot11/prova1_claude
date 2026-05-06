# apps/web — UFI Frontend

React + Vite + TS + MapLibre + deck.gl + Tailwind + Zustand.

## Layout

```
src/
  main.tsx        Entry, render root.
  App.tsx         Layout actual (mapa placeholder + sidebar). Reemplazar con MapLibre.
  api.ts         Cliente tipado contra apps/api (espejo de schemas.py).
  store.ts       Zustand: mode, at, selectedBarrio.
  index.css       Tailwind base.
```

## Comandos

```powershell
cd apps/web
npm install
npm run dev          # http://localhost:3000
npm run build
```

`vite.config.ts` proxea `/api` → `http://localhost:8000`. En prod, `VITE_API_BASE_URL` apunta a Railway.

## Reglas duras

- **`api.ts` es espejo de `apps/api/app/schemas.py`**. Si el back rompe contrato, romper aquí también — no hacer adapters.
- **Idiomas**: identificadores en inglés, textos al usuario en castellano.
- **Timestamps**: ISO 8601 UTC desde la API, formatear a `Europe/Madrid` solo al renderizar.
- **No fetchear en cada hover**: paneles cargan al `click`, no al `mouseenter`.
- **Persona A es propietaria** de `App.tsx` y de toda la sub-carpeta de componentes que cree.

## Tareas Persona A

- [ ] Mapa MapLibre con layer choropleth de barrios (deck.gl `GeoJsonLayer`).
- [ ] Capa toggleable de tramos viarios (deck.gl `PathLayer`).
- [ ] Slider horario +0h..+48h en topbar.
- [ ] Bar chart contribuciones (recharts o div tags + Tailwind).
- [ ] Selector de modos (chips, ya hay placeholder en App.tsx).
- [ ] Comparador "ahora vs +3h" (flechas ↑↓ por barrio).

## Diseño

- Paleta UFI: `bg-ufi-low` (verde) → `bg-ufi-mid` (ámbar) → `bg-ufi-high` (rojo) → `bg-ufi-critical`.
- Tipografía system-ui, sin imports externos.
- Mobile: el mapa pasa a top, sidebar abajo (responsive ≥md).
