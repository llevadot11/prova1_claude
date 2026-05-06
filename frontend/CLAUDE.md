# Persona A — Frontend & Visualización

**Tu carpeta**: `frontend/`
**Tu único contacto de contrato**: [src/api.ts](src/api.ts) — es el espejo de `backend/app/schemas.py`. Si hay cambio en el contrato, B te avisa.

---

## Tu rol en el equipo

Eres el dueño de todo lo que el jurado VE. El producto se gana o se pierde en esta carpeta. Tu trabajo es el mapa interactivo, el panel lateral, las animaciones y la paleta visual.

---

## Stack

| Herramienta | Para qué |
|---|---|
| React 18 + Vite + TS | Base del proyecto |
| **MapLibre GL JS** | Mapa base (sin API key, Open Source) |
| **deck.gl** | Capas de datos encima del mapa: choropleth barrios, líneas de tramos |
| Tailwind CSS | Estilos rápidos, paleta UFI ya configurada |
| Zustand | Estado global: `mode`, `at` (slider), `selectedBarrio` |

---

## Comandos

```powershell
# Desde la carpeta frontend/
npm install
npm run dev      # http://localhost:3000
npm run build    # para deploy en Vercel
npm test
```

La API está proxeada en `/api` → `http://localhost:8000`. Necesitas que B arranque el backend.
Si B no está disponible, el backend stub ya devuelve datos dummy correctos.

---

## Estructura de ficheros

```
frontend/
  src/
    App.tsx         Layout base. REEMPLAZAR con mapa real.
    api.ts         Cliente tipado (NO modificar sin avisar a B).
    store.ts       Zustand: mode, at, selectedBarrio.
    index.css       Tailwind imports.
  package.json
  vite.config.ts  (proxy /api → :8000)
  tailwind.config.js
  vercel.json
  tasks.md        ← TU LISTA DE TAREAS
  skills.md       ← Subagentes y skills útiles
```

## Paleta de colores UFI

Ya configurada en `tailwind.config.js`:
- `bg-ufi-low` → verde `#22c55e` (UFI < 30)
- `bg-ufi-mid` → ámbar `#f59e0b` (30–60)
- `bg-ufi-high` → rojo `#ef4444` (60–80)
- `bg-ufi-critical` → rojo oscuro `#7f1d1d` (> 80)

---

## Datos que recibes de la API

| Endpoint | Cuándo lo usas |
|---|---|
| `GET /ufi?at=&mode=` | Cada vez que cambia el slider o el modo |
| `GET /tramos/state?at=` | Para capa secundaria de tramos |
| `GET /barrio/{id}?at=&mode=` | Al clickar un barrio en el mapa |
| `GET /explain/{id}?at=&mode=` | Al clickar un barrio (panel texto) |
| `GET /modes` | Para pintar los botones de modos |
| `GET /barrios` | Una sola vez al montar la app (GeoJSON) |
| `GET /tramos` | Una sola vez al activar la capa |

---

## Reglas de coordinación

- **NO modificar `api.ts`** sin acordarlo con B. Es el contrato.
- **Timestamps**: recibes ISO 8601 UTC. Formatea a `Europe/Madrid` solo al renderizar.
- **No fetchear en cada hover**: el panel se carga en `onClick`, no en `onMouseEnter`.
- Si `/explain` tarda (Claude), muestra spinner y el bar chart mientras espera.

---

## Subagents que puedes pedir a Claude Code

Ver [skills.md](skills.md). Resumen:
- `Explore` → *"¿Cómo se usa GeoJsonLayer de deck.gl para colorear polígonos?"*
- `claude-code-guide` → dudas sobre React hooks, Zustand, TypeScript
- `general-purpose` → *"Escríbeme el componente MapView completo con MapLibre + deck.gl"*
- `Plan` → si necesitas replantear un componente complejo antes de codear
