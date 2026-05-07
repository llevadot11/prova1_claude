import { useCallback, useMemo } from "react";
import DeckGL from "@deck.gl/react";
import { GeoJsonLayer } from "@deck.gl/layers";
import type { PickingInfo } from "@deck.gl/core";
import Map from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection, Feature } from "geojson";
import { ufiToColor, UFI_LEGEND } from "../utils/ufiColor";
import type { BarrioUFI } from "../api";
import { useUFI } from "../store";

const INITIAL_VIEW_STATE = {
  longitude: 2.169,
  latitude: 41.389,
  zoom: 12,
  pitch: 0,
  bearing: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// Constantes fuera del componente: referencia estable, deck.gl no detecta cambios espurios
const DECK_STYLE = { position: "relative" as const, width: "100%", height: "100%" };
const WRAPPER_STYLE = { position: "relative" as const, width: "100%", height: "100%" };
const BORDER_COLOR: [number, number, number, number] = [255, 255, 255, 40];
const FALLBACK_COLOR: [number, number, number, number] = [100, 100, 100, 150];

const TRAM_COLORS: Record<number, [number, number, number, number]> = {
  1: [45,  212, 191, 230],
  2: [132, 204, 22,  230],
  3: [251, 191, 36,  230],
  4: [251, 146, 60,  230],
  5: [248, 113, 113, 230],
  6: [50,  50,  50,  230],
};

interface Props {
  barrios: FeatureCollection | null;
  ufiScores: Record<string, BarrioUFI>;
  tramosGeo?: FeatureCollection | null;
  tramoStates?: Record<number, number>;
}

export default function MapView({
  barrios,
  ufiScores,
  tramosGeo,
  tramoStates,
}: Props) {
  // Selector específico: MapView solo se re-renderiza si selectBarrio cambia (nunca ocurre)
  const selectBarrio = useUFI((s) => s.selectBarrio);

  const layers = useMemo(
    () => [
      ...(barrios
        ? [
            new GeoJsonLayer({
              id: "barrios-choropleth",
              data: barrios,
              pickable: true,
              stroked: true,
              filled: true,
              getFillColor: (f: Feature) => {
                const id = f.properties?.barrio_id as string | undefined;
                const s = id ? ufiScores[id] : undefined;
                return s ? ufiToColor(s.ufi) : [30, 36, 53, 80];
              },
              getLineColor: BORDER_COLOR,
              getLineWidth: 1,
              lineWidthMinPixels: 1,
              updateTriggers: { getFillColor: ufiScores },
              transitions: { getFillColor: 400 },
              onClick: (info: PickingInfo) => {
                const id = (info.object as Feature | null)?.properties
                  ?.barrio_id as string | undefined;
                if (id) selectBarrio(id);
              },
            }),
          ]
        : []),
      ...(tramosGeo && tramoStates
        ? [
            new GeoJsonLayer({
              id: "tramos-layer",
              data: tramosGeo,
              pickable: false,
              stroked: false,
              filled: false,
              getLineColor: (f: Feature) => {
                const tram_id = f.properties?.tram_id as number | undefined;
                const state =
                  tram_id !== undefined ? tramoStates[tram_id] : undefined;
                return TRAM_COLORS[state ?? 0] ?? FALLBACK_COLOR;
              },
              getLineWidth: 3,
              lineWidthMinPixels: 2,
              updateTriggers: { getLineColor: tramoStates },
            }),
          ]
        : []),
    ],
    // selectBarrio es una referencia estable de Zustand, no necesita estar en deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [barrios, ufiScores, tramosGeo, tramoStates]
  );

  const getTooltip = useCallback(
    ({ object }: PickingInfo) => {
      if (!object) return null;
      const id = (object as Feature).properties?.barrio_id as string | undefined;
      const s = id ? ufiScores[id] : undefined;
      return s ? `${s.barrio_name} — UFI ${s.ufi.toFixed(0)}` : null;
    },
    [ufiScores]
  );

  const handleClick = useCallback(
    (info: PickingInfo) => {
      if (!info.object) selectBarrio(null);
    },
    [selectBarrio]
  );

  return (
    <div style={WRAPPER_STYLE}>
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        getTooltip={getTooltip}
        onClick={handleClick}
        style={DECK_STYLE}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>

      {/* Leyenda flotante */}
      <div className="absolute bottom-8 left-4 z-10 rounded-card bg-surface-2/85 backdrop-blur-glass border border-surface-border shadow-glass px-3 py-2.5 pointer-events-none">
        <p className="text-[9px] uppercase tracking-widest text-content-muted mb-2 font-medium">
          Índice UFI
        </p>
        {UFI_LEGEND.map(({ label, range, color }) => (
          <div key={label} className="flex items-center gap-2 mb-1.5 last:mb-0">
            <span
              className="w-2.5 h-2.5 rounded-sm shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="text-[11px] text-content-secondary">{label}</span>
            <span className="text-[10px] text-content-muted ml-auto pl-3 tabular-nums">
              {range}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
