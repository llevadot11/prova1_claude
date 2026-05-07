# UFI Barcelona — Índice de Fricción Urbana

## What this is

UFI Barcelona is a public-facing urban diagnostic that answers a single question for any moment in the next 24 hours:

> *¿Qué zonas de Barcelona estarán peor para moverse, y por qué?*

It fuses live traffic, weather, air quality, accident history, and points of interest into a 0–100 friction index per neighbourhood (73 barris) and per hour, with a natural-language explanation. Users move a time slider, switch a movement profile (default / familiar / runner / movilidad reducida), and the map repaints.

## Register

**product** — the design serves the function. The map IS the product. Chrome around the map is supporting tissue, not the centerpiece.

## Users

Three concrete audiences, in priority order:

1. **Curious BCN citizen on a Saturday morning** — opening on a phone or laptop before leaving the flat. Wants a fast answer ("is el Raval terrible right now?") and maybe a why. Not a power user. Not a planner. Will leave in 90 seconds if the page feels generic or untrustworthy.
2. **Mobility / urban-planning observer** — journalist, council staffer, NGO researcher. Wants to compare neighbourhoods, scrub the timeline, screenshot for a report. Cares about provenance and units.
3. **Hackathon jury (week of 2026-05-09)** — five minutes, watching a guided demo. Needs to *immediately read* what the map is saying without anyone explaining the legend. Aesthetic credibility decides the score as much as accuracy.

## Product purpose

Make a half-second-readable picture of a city's friction *right now and soon*, sourced from real public data, with explanations a non-specialist can repeat in their own words. The thing the user takes away is **a mental map of where to avoid**, not a dashboard reading.

## Strategic principles

- **The map is the document.** Everything else (header, sidebar, legend, time slider) reads as marginalia around a printed map. Treat the canvas like a survey poster, not a SaaS panel.
- **Read in one glance, learn in three.** A user who looks for one second should know which areas are bad. A user who looks for three seconds should know *why this area, this hour*.
- **Civic, not corporate.** This is a public-good tool about a real city. The visual language belongs to urban planning documents and public signage, not to B2B dashboards.
- **Provenance visible.** Real data, real units, named sources. The demo should never feel like placeholder JSON.
- **Fast over fancy.** No animation that delays comprehension. No motion on layout properties. Map repaint must feel instant (<150ms perceived) when the slider moves.

## Tone

Civic, plainspoken, slightly editorial. Spanish is the user-facing language; identifiers stay English. Numbers are units, not decorations. No marketing language. No "AI-powered." No emoji. No exclamation marks.

Voice references: a well-typeset metro map legend; a Catalan urban-planning report; the back of a Pla Especial document. Quiet authority.

## Anti-references — what this MUST NOT look like

These are absolute. The current build fails most of them.

- **Generic AI / SaaS dashboard.** Dark navy + teal/cyan accent + glass cards + "TOP 10" floating panel + lucide icons everywhere = the exact template the user explicitly rejected. The aesthetic that screams "an LLM made this." Avoid every signal of it.
- **Observability tool.** Grafana / Datadog / Linear-dark-clone vibe. Wrong category — this is not infrastructure monitoring.
- **Citymapper / Google Maps clone.** Don't imitate consumer route planners. UFI is not navigation.
- **Bloomberg / trading terminal.** Dense rows of numbers in monospace on black. Wrong audience.
- **Glassmorphism, gradient text, hero-metric cards, side-stripe accents, neon-on-dark, frosted overlays.** All banned by the shared design laws and by user direction.
- **Lucide icon next to every label.** Currently the header has icons next to "MapPin", "Layers", chips. Decoration without affordance. Strip ruthlessly.
- **"Indice de Friccion Urbana" as a small subtitle in a 10px gray under a tiny logo chip.** Reads as boilerplate. Either commit to a real masthead or remove the subtitle.

## Visual lineage (positive references — direction, not copy)

- Pla Cerdà printed survey maps; Catalan urban-planning posters from the 70s–90s.
- ETH Zürich / Swiss federal mapping bureau publication style — generous margins, thin rules, named legend, restrained color.
- Stamen Toner / Toner Lite cartography — high-contrast, ink-on-paper map feel.
- The New York Times graphics desk's Barcelona / Madrid pieces — editorial maps with sober annotation, not dashboards.

## Constraints

- 73 neighbourhood polygons rendered via deck.gl GeoJsonLayer over MapLibre. The choropleth must remain readable at every zoom from "all of BCN" to "single barri."
- Time slider must feel like a *physical* control. Scrubbing it should feel responsive even with API in flight.
- Mode switch (4 presets) must be visually obvious without lucide icons.
- Tramos viarios is a secondary toggleable layer. Off by default.
- Demo runs offline-capable (snapshot fallback). The "Demo" badge must look intentional, not like an error.
- Mobile: at minimum readable on 390px (iPhone). Sidebar collapses to a sheet.

## Success — what "good" looks like

1. The screenshot, with no caption, reads as "a Barcelona environmental survey" not "an AI app."
2. A jury member who has never seen the project understands the legend, the slider, and the mode switch in under 10 seconds without narration.
3. A citizen on a phone can identify the worst three neighbourhoods right now in one tap.
4. None of the absolute bans appear in the rendered DOM.
