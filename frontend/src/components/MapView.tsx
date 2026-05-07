import { useCallback, useMemo } from "react";
import DeckGL from "@deck.gl/react";
import { GeoJsonLayer } from "@deck.gl/layers";
import type { PickingInfo } from "@deck.gl/core";
import Map from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection, Feature } from "geojson";
import { ufiToColor } from "../utils/ufiColor";
import type { BarrioUFI } from "../api";
import { useUFI } from "../store";
import Legend from "./Legend";

const INITIAL_VIEW_STATE = {
  longitude: 2.169,
  latitude: 41.389,
  zoom: 12,
  pitch: 0,
  bearing: 0,
};

// Carto Positron — light ink-on-paper basemap. Closest free MapLibre style to
// Stamen Toner Lite without an extra dependency.
const PRIMARY_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

// Offline / strict-no-network fallback: minimal MapLibre style with paper land,
// no tiles, no labels. Activated when DEMO_OFFLINE flag is set OR the primary
// style fetch fails.
const FALLBACK_STYLE = {
  version: 8 as const,
  name: "ufi-paper-fallback",
  sources: {},
  layers: [
    {
      id: "paper",
      type: "background" as const,
      paint: { "background-color": "#f7f5ee" },
    },
  ],
  glyphs: undefined,
  sprite: undefined,
};

const MAP_STYLE: string | typeof FALLBACK_STYLE =
  import.meta.env.VITE_DEMO_OFFLINE === "1" ? FALLBACK_STYLE : PRIMARY_STYLE;

const DECK_STYLE = {
  position: "absolute" as const,
  top: "0",
  left: "0",
  right: "0",
  bottom: "0",
};
const WRAPPER_STYLE = {
  position: "absolute" as const,
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  overflow: "hidden" as const,
  backgroundColor: "#f7f5ee",
};
const STABLE_DPR =
  typeof window !== "undefined" ? Math.max(1, Math.floor(window.devicePixelRatio || 1)) : 1;

const POLYGON_STROKE: [number, number, number, number] = [42, 38, 30, 140];
const POLYGON_STROKE_HOVER: [number, number, number, number] = [42, 38, 30, 230];
const FALLBACK_FILL: [number, number, number, number] = [232, 226, 210, 90];

const TRAM_RGB: Record<number, [number, number, number, number]> = {
  1: [155, 198, 167, 230],
  2: [178, 219, 200, 230],
  3: [220, 198, 130, 230],
  4: [212, 154,  79, 230],
  5: [196, 102,  60, 230],
  6: [120, 110,  95, 200],
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
  const selectBarrio = useUFI((s) => s.selectBarrio);
  const selectedId = useUFI((s) => s.selectedBarrio);

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
                return s ? ufiToColor(s.ufi) : FALLBACK_FILL;
              },
              getLineColor: (f: Feature) => {
                const id = f.properties?.barrio_id as string | undefined;
                return id && id === selectedId ? POLYGON_STROKE_HOVER : POLYGON_STROKE;
              },
              getLineWidth: (f: Feature) => {
                const id = f.properties?.barrio_id as string | undefined;
                return id && id === selectedId ? 2.5 : 0.6;
              },
              lineWidthMinPixels: 1,
              lineWidthUnits: "pixels",
              updateTriggers: {
                getFillColor: ufiScores,
                getLineColor: selectedId,
                getLineWidth: selectedId,
              },
              transitions: { getFillColor: 220 },
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
              pickable: true,
              stroked: false,
              filled: false,
              getLineColor: (f: Feature) => {
                const props = f.properties ?? {};
                const tram_id =
                  (props.tram_id as number | undefined) ??
                  (props.idTram as number | undefined);
                const state =
                  tram_id !== undefined ? tramoStates[tram_id] : undefined;
                return TRAM_RGB[state ?? 0] ?? [120, 110, 95, 200];
              },
              getLineWidth: 2.4,
              lineWidthMinPixels: 1.5,
              updateTriggers: { getLineColor: tramoStates },
            }),
          ]
        : []),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [barrios, ufiScores, tramosGeo, tramoStates, selectedId]
  );

  const getTooltip = useCallback(
    ({ object }: PickingInfo) => {
      if (!object) return null;
      const props = (object as Feature).properties ?? {};
      const id = props.barrio_id as string | undefined;
      const s = id ? ufiScores[id] : undefined;
      if (!s) return null;
      const district = s.district_name ? ` · ${s.district_name}` : "";
      return {
        text: `${s.barrio_name}${district}\nUFI ${s.ufi.toFixed(0)}`,
        style: {
          backgroundColor: "#f7f5ee",
          color: "#2a2620",
          border: "1px solid #c7bfa9",
          borderRadius: "0",
          padding: "6px 10px",
          fontFamily: '"Inter Tight", Inter, system-ui, sans-serif',
          fontSize: "12px",
          fontWeight: "500",
          boxShadow: "0 2px 6px -2px rgba(60, 50, 30, 0.18)",
          whiteSpace: "pre-line",
        },
      };
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
        useDevicePixels={STABLE_DPR}
      >
        <Map mapStyle={MAP_STYLE as never} reuseMaps />
      </DeckGL>

      <div className="absolute bottom-6 left-6 z-10 pointer-events-none">
        <Legend />
      </div>
    </div>
  );
}
