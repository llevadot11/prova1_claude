# Guion de demo — 3 minutos

## 0:00–0:20 — Hook
> *"¿Qué barrios de Barcelona estarán peor para moverse hoy a las 18h y por qué? Hasta ahora nadie te lo dice. Esto sí."*
- Mostrar mapa con todos los barrios coloreados.

## 0:20–0:50 — UFI vivo
- Click en barrio peor puntuado (top de la lista).
- Aparece score, bar chart de contribuciones, frase natural Claude.
- *"El score combina 5 familias: tráfico, accidentes históricos, aire, meteo y puntos sensibles."*

## 0:50–1:30 — Slider temporal
- Mover slider +3h. Mapa se anima. Aparecen flechas ↑/↓ por barrio.
- *"Esto es predicción horaria a 48h, calibrada con varios meses de TRAMS reales y modelos LightGBM."*

## 1:30–2:10 — Modos de usuario
- Cambiar a "familiar". Ranking cambia visiblemente.
- *"Mismo dato, otra persona, otra ciudad. Familiar pondera más colegios y aire."*
- Cambiar a "runner". Volver a "default".

## 2:10–2:40 — Capa tramos
- Toggle de tramos viarios. Aparecen líneas coloreadas.
- *"Bajamos a la calle: predicción TRAMS por tramo viario."*

## 2:40–3:00 — Cierre
- *"Open data, modelos LightGBM, explicación natural con Claude. Construido en 48h."*
- Mostrar URL pública.

## Plan B
- Si cae wifi → activar `DEMO_OFFLINE=1`, demo sigue corriendo del snapshot.
- Si cae el portátil → vídeo grabado en `demo/recording.mp4`.
