# UFI Barcelona — Design System

Companion to PRODUCT.md. Where PRODUCT.md sets the *what*, this sets the *how it looks and moves*.

## North star

Print urban-planning document made interactive. Paper, ink, hairline rules, named legend, sober numerics. Not a dashboard.

## Theme decision

**Light, paper-tinted.** Not "light mode for safety." The scene that forces it:

> A BCN resident at 9am on a Saturday at the kitchen table, phone or laptop, daylight through a window. Or a council researcher on a 24-inch monitor at noon. Or a jury member in a well-lit hackathon room. None of these are dim-room scenes. None of these benefit from dark navy. Dark mode here would copy the AI-dashboard reflex the user explicitly rejected.

A subtle paper warmth (off-white at L≈98, chroma ≈0.005 toward yellow) immediately separates this from the cool-slate dark-mode default. The map area itself uses near-white with an ink-gray basemap — the cartography reads as a printed plate, not a screen layer.

## Color strategy

**Restrained**, with a single committed semantic ramp for the UFI scale.

### Neutrals (paper + ink)

All OKLCH. Tinted toward a warm yellow-gray to evoke aged plan paper, never `#fff` or `#000`.

| Token | OKLCH | Use |
|---|---|---|
| `paper` | `oklch(0.985 0.005 95)` | Page background |
| `paper-2` | `oklch(0.965 0.006 95)` | Sidebar / annotation column |
| `paper-3` | `oklch(0.93 0.008 90)` | Hover, subtle fills |
| `rule` | `oklch(0.82 0.01 85)` | Hairline rules (1px) |
| `rule-strong` | `oklch(0.62 0.012 80)` | Stronger rules (2px masthead) |
| `ink-3` | `oklch(0.55 0.01 80)` | Tertiary text, captions |
| `ink-2` | `oklch(0.38 0.012 80)` | Secondary text |
| `ink` | `oklch(0.20 0.015 80)` | Primary text, headlines |

### UFI scale (the only chromatic system)

A perceptually-uniform ramp from low-friction (cool, calm) to critical (warm, urgent). **Earthy, not neon.** Tuned for printed-map readability over polygon fills with 75% opacity on paper.

| Stop | Range | OKLCH | Reads as |
|---|---|---|---|
| `ufi-0` | 0–14 | `oklch(0.86 0.06 165)` | Pale sage |
| `ufi-1` | 15–29 | `oklch(0.78 0.09 150)` | Muted moss |
| `ufi-2` | 30–44 | `oklch(0.84 0.11 95)` | Wheat |
| `ufi-3` | 45–59 | `oklch(0.76 0.14 70)` | Ochre |
| `ufi-4` | 60–74 | `oklch(0.65 0.17 45)` | Burnt sienna |
| `ufi-5` | 75–100 | `oklch(0.48 0.18 30)` | Iron oxide red |

No teal. No saturated emerald. No pure red. The scale must feel pigment-printed.

### Accent (used sparingly, ≤5% of surface)

`accent-ink` `oklch(0.32 0.05 240)` — a deep prussian blue, used only for active state of the time slider handle and selected mode. Single accent, no gradients.

## Typography

Three families, loaded from Google Fonts with `display=swap`. Each has a clear job — no hierarchy collapses to "use Inter for everything."

| Family | Role | Weights | Notes |
|---|---|---|---|
| **Instrument Serif** | Display, masthead, large barri names in panel | 400, 400 italic | Editorial. Carries the "civic document" voice. |
| **Inter Tight** | UI, body, labels, buttons | 400, 500, 600 | Workhorse. Clean grotesque. |
| **JetBrains Mono** | Numerics — UFI score, coords, timestamps | 400, 500 | Tabular figures on. Numbers always mono so columns align. |

### Scale (modular, ratio ~1.28)

```
display-2xl  56px / 1.0   Instrument Serif 400         Masthead "UFI Barcelona"
display-xl   40px / 1.05  Instrument Serif 400 italic  Selected barri name
display-lg   28px / 1.15  Instrument Serif 400         Section headlines
body-lg      17px / 1.5   Inter Tight 400              Explanation text
body         14px / 1.45  Inter Tight 400              UI default
body-sm      13px / 1.4   Inter Tight 500              Labels
caption      11px / 1.3   Inter Tight 500 / 0.04em     ALL CAPS keys, legend headings
mono-lg      24px / 1.0   JetBrains Mono 500           UFI score in panel
mono         13px / 1.1   JetBrains Mono 500           Inline numerics, deltas
```

Body line length capped at 65ch. No gradient text, no outline text, no wide letter-spacing on body.

## Layout

### Spatial system

8px grid, but used with rhythm — not "everything 16px." Paper layouts breathe. Margin-as-page beats margin-as-component.

- Page outer gutter: **32px desktop / 16px mobile**.
- Vertical rhythm between sections: **40–56px** (varies for emphasis).
- Sidebar inner padding: **20px horizontal, 14–24px vertical** depending on section.
- Map inset: 1px hairline rule, 0px padding (map fills its frame edge-to-edge).

### Surfaces

The page has only three surfaces. **No nested cards. No glass. No floating panels with shadow + border + backdrop-blur.**

1. **Masthead** — full-bleed, paper-2 background, single 2px ink rule below. Holds title, mode register, demo badge, time scrubber.
2. **Map plate** — paper background, 1px rule frame, fills the viewport's main column. Legend is a printed key in the bottom-left corner of the plate (not a card — just typeset on the paper).
3. **Annotation column** — right column on desktop (320–360px), separated from the map plate by a 1px rule. NOT a floating panel. NOT rounded. NOT blurred. Just a column. On mobile it becomes a bottom sheet.

### Cards: avoided.

There are no card components in this design. List rows in the ranking are separated by 1px rules, not boxed. The barri detail is a typeset article, not a card stack.

## Motion

- Choropleth recoloring: 180ms `cubic-bezier(0.22, 1, 0.36, 1)` (ease-out-quart). Color only, never position.
- Time slider handle: 1:1 with pointer, no easing on drag. After release, snap with 120ms ease-out-quart.
- Annotation column entrance (when a barri is selected): 220ms opacity + 8px Y translate, ease-out-quart. No slide-in from edges, no spring.
- Hover state on ranking rows: 80ms background fade, no transform.
- **Banned**: bounce, spring, elastic, scale on hover, shimmer, skeleton pulse on the map area.

## Iconography

**Almost none.** Lucide icons are mostly removed. The only icons that survive:

- A single 16px chevron for the back-arrow in the barri detail view.
- A 14px caret on the time-slider handle (printed-document mark, not Material).
- The "Tramos" toggle is a labeled switch, no icon.

No icon next to "UFI Barcelona" masthead. No icon next to mode chips. No `MapPin` chip. The map IS the location indicator.

## Components

### Mode register (replaces "mode chips")

Reads as the table of contents of a planning document. Four modes laid out as a horizontal label list, separated by a thin vertical rule. The active mode is set in `ink` weight 600, the others in `ink-3` weight 400. No pills, no borders, no background fills.

```
Por defecto  │  Familiar  │  Runner  │  Movilidad reducida
```

Underlined with a 2px `accent-ink` rule under the active item only.

### Time scrubber

Horizontal axis with tick marks at every 3 hours over a 24-hour window. Hour numerals in JetBrains Mono caption size. Active position marked by a 2px `accent-ink` vertical rule with the timestamp set inline above in body-sm. Quick-jump controls (`Ahora`, `+1h`, `+3h`, `+6h`, `+12h`, `+24h`) become inline links beneath the axis, not pills.

### Demo badge

A small typeset notice at the right edge of the masthead: `MODO DEMO · datos cacheados` in caption size, ink-3, with a 1px ochre rule on the left. Not an alert, not amber neon. Reads as a footnote.

### Ranking list (annotation column)

Numbered list 01–10, monospace numbers left, barri name in body, UFI value in mono-lg right-aligned, all separated by 1px rules. Selected row indents 4px and gets a 2px `accent-ink` left rule (the ONE place a left rule is permitted because it is structural — selection, not decoration).

### Barri detail

Replaces the ranking when a barri is selected. Reads as a single-page article:

1. Barri name in `display-xl` italic Instrument Serif.
2. UFI value in `mono-lg` next to a one-word qualifier ("Fluido", "Moderado", "Alto", "Crítico") in `caption`.
3. A short typeset paragraph (the natural-language explanation from `/explain`).
4. A horizontal contribution chart — bars rendered as filled rules with the ufi-* color of the contribution magnitude, label and value typeset to either side. No grid lines, no axis labels beyond min/max.
5. Provenance line at the bottom in caption ink-3: data sources and timestamp.

### Legend

Printed corner key, no background. Six rules of color stacked vertically, each 24×6px, with the range numerals in mono caption beside.

```
0–14    [██]  Fluido
15–29   [██]  Bajo
30–44   [██]  Moderado
45–59   [██]  Alto
60–74   [██]  Muy alto
75–100  [██]  Crítico
```

## Map basemap

MapLibre style replaced. Goal: ink-on-paper cartography. Land = paper, water = paper-2, roads = ink-3 hairlines, labels = Inter Tight 11px in ink-2. No satellite tiles, no street-level detail competing with the choropleth. The reference is **Stamen Toner Lite tinted toward warm**, not the default OSM raster.

## Responsive

- ≥1280px: masthead + map plate + 360px annotation column.
- 768–1279px: masthead + map plate + 320px annotation column.
- <768px: masthead collapses to title + mode dropdown + scrubber stacked. Annotation becomes a bottom sheet (drag handle, 50/100% snap points).

## Accessibility

- Color is never the only signal. The UFI ramp is also encoded as the numeric value (always visible on selection), and as ordinal in the legend.
- Contrast: ink/paper ≥ 12:1, ink-2/paper ≥ 7:1, ink-3/paper ≥ 4.5:1. Verified.
- Slider operable by keyboard with arrow keys (1h step) and PgUp/PgDn (3h step).
- Map polygons have an accessible name (barri name + UFI value) for screen readers via `aria-label` on the SVG layer fallback.

## What this design rejects

For the avoidance of doubt:

- Dark mode of any kind on the page surface. (Map basemap is light too.)
- Glass cards, backdrop blur on UI elements (one allowed exception: nothing).
- Lucide / Heroicons / Phosphor decorative icons.
- Pill chips with rounded-full and brand-tinted backgrounds.
- Gradient anywhere, including text and buttons.
- Card components nested in card components.
- Bouncy / spring / elastic motion.
- Em dashes in copy.
- The current `slide-in` animation, the `backdrop-blur-glass` class, the `shadow-glass` token. To be removed from `tailwind.config.js`.
