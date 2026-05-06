# Skills & Subagents — Persona A (Frontend)

> Cómo sacarle el máximo partido a Claude Code desde tu carpeta.
> Abre Claude Code con `claude` desde `frontend/`.

---

## Subagentes que puedes lanzar

Claude Code puede lanzar agentes especializados con el tool `Agent`. Pídelos en lenguaje natural en el chat.

### `Explore` — búsqueda rápida en el código
**Úsalo cuando**: no sabes dónde está algo o quieres entender cómo funciona una librería.
```
Ejemplos de lo que puedes pedir:
"¿Cómo se usa GeoJsonLayer de deck.gl para colorear polígonos con una escala de color?"
"¿Qué métodos tiene el store de Zustand que ya tenemos en store.ts?"
"¿Cómo funciona el proxy de Vite en vite.config.ts?"
"Busca todos los usos de useEffect en la carpeta src/"
```

### `general-purpose` — escribir código complejo
**Úsalo cuando**: necesitas un componente completo o una implementación que requiere varios ficheros.
```
Ejemplos:
"Escríbeme el componente MapView.tsx con MapLibre + deck.gl GeoJsonLayer,
 coloreando cada barrio según su ufi usando la paleta de tailwind.config.js"

"Escríbeme el componente TimeSlider.tsx con un input range que genera
 los labels +0h..+47h y llama a setAt del store cuando el valor cambia"

"Escríbeme el componente ContribBar.tsx que recibe la lista de FamilyContribution
 y pinta barras horizontales coloreadas por familia"
```

### `claude-code-guide` — preguntas sobre herramientas
**Úsalo cuando**: tienes dudas técnicas sobre React, TypeScript, deck.gl, MapLibre.
```
"¿Cómo hago que un GeoJsonLayer de deck.gl se actualice cuando cambia el estado de Zustand?"
"¿Cuál es la diferencia entre react-map-gl y usar MapLibre GL JS directamente?"
"¿Cómo funciona el ViewState de deck.gl para combinar con MapLibre?"
```

### `Plan` — planificación antes de codear
**Úsalo cuando**: no tienes claro cómo estructurar un componente complejo.
```
"Quiero hacer el comparador 'ahora vs +3h' con flechas ↑↓ por barrio en el mapa.
 No sé si poner la lógica en el componente o en el store. ¿Qué arquitectura me recomiendas?"
```

---

## Slash commands útiles

Invócalos escribiendo `/nombre` en el chat de Claude Code.

| Comando | Cuándo usarlo |
|---|---|
| `/review` | Antes de decirle a D que hay algo listo para integrar. Revisa el código de tu PR. |
| `/simplify` | Si tienes un componente que parece demasiado complejo. Sugiere simplificaciones. |
| `/security-review` | Si usas `dangerouslySetInnerHTML` o manejas datos del usuario. |

---

## Patrones de prompt que funcionan bien

### Para construir un componente visual
```
"Crea src/components/MapView.tsx. Requisitos:
- MapLibre GL JS con estilo carto (libre)
- deck.gl DeckGL overlay encima del mapa
- GeoJsonLayer que colorea los polígonos de barrios según su UFI
- La función de color debe usar la paleta de tailwind.config.js
- Al hacer click en un polígono llama a selectBarrio(barrio_id) del store
- TypeScript strict, sin any"
```

### Para debug de un problema
```
"El mapa no se actualiza cuando el slider cambia. El store tiene el valor correcto
(lo veo en React DevTools), pero el GeoJsonLayer no re-renderiza.
Aquí está el componente: [pega el código]"
```

### Para conectar con la API
```
"Hay un bug: cuando hago fetch a /ufi con el token `at` en formato ISO 8601,
a veces el back devuelve 400 con 'Invalid at'. Aquí está api.ts línea 45
y el error de la consola: [pega el error]"
```

---

## Reglas para no perder tiempo

1. **Lee `tasks.md` antes de pedir código**. Describe la tarea en contexto.
2. **Cita siempre el fichero y línea** cuando reportas un bug.
3. **Pide un fichero a la vez**, no "escríbeme toda la app".
4. **El stub del backend ya funciona** — puedes trabajar sin C ni B.
