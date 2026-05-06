import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Layers,
  Loader2,
  MapPin,
  MousePointer2,
  WifiOff,
  X,
} from "lucide-react";
import type { FeatureCollection } from "geojson";
import { api, type BarrioUFI, type ModePreset } from "./api";
import { useUFI } from "./store";
import { ufiChipClass } from "./utils/ufiColor";
import MapView from "./components/MapView";
import TimeSlider from "./components/TimeSlider";
import BarrioPanel from "./components/BarrioPanel";

export default function App() {
  const { mode, at, setMode, selectedBarrio, selectBarrio } = useUFI();

  const [barriosGeo, setBarriosGeo] = useState<FeatureCollection | null>(null);
  const [barrios, setBarrios] = useState<BarrioUFI[]>([]);
  const [modes, setModes] = useState<ModePreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showTramos, setShowTramos] = useState(false);
  const [tramosGeo, setTramosGeo] = useState<FeatureCollection | null>(null);
  const [tramoStates, setTramoStates] = useState<Record<number, number>>({});
  const tramosLoadedRef = useRef(false);

  const [comp3h, setComp3h] = useState<Record<string, number>>({});
  const [degraded, setDegraded] = useState<boolean | null>(null);

  useEffect(() => {
    api.barrios().then(setBarriosGeo).catch(console.error);
    api.modes().then(setModes).catch(console.error);
    api
      .health()
      .then((h) =>
        setDegraded(
          h.demo_offline === true || Object.values(h).some((v) => v === "down")
        )
      )
      .catch(() => setDegraded(true));
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .ufi(at ?? undefined, mode)
      .then((res) => { setBarrios(res.barrios); setError(null); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [mode, at]);

  useEffect(() => {
    setComp3h({});
    const base = at ? new Date(at) : new Date();
    base.setHours(base.getHours() + 3);
    api
      .ufi(base.toISOString(), mode)
      .then((res) =>
        setComp3h(Object.fromEntries(res.barrios.map((b) => [b.barrio_id, b.ufi])))
      )
      .catch(console.error);
  }, [mode, at]);

  useEffect(() => {
    if (!showTramos || tramosLoadedRef.current) return;
    tramosLoadedRef.current = true;
    api.tramos().then(setTramosGeo).catch(console.error);
  }, [showTramos]);

  useEffect(() => {
    if (!showTramos) return;
    api
      .tramosState(at ?? undefined)
      .then((res) =>
        setTramoStates(Object.fromEntries(res.tramos.map((t) => [t.tram_id, t.state])))
      )
      .catch(console.error);
  }, [showTramos, at]);

  const ufiMap = useMemo<Record<string, BarrioUFI>>(
    () => Object.fromEntries(barrios.map((b) => [b.barrio_id, b])),
    [barrios]
  );

  const ranked = useMemo(
    () => [...barrios].sort((a, b) => b.ufi - a.ufi),
    [barrios]
  );

  return (
    <div className="flex flex-col h-full bg-surface-base font-sans">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="shrink-0 flex flex-col bg-surface-1 border-b border-surface-border z-30">

        {/* Row 1: Branding + controles */}
        <div className="flex items-center gap-4 px-5 h-12 border-b border-surface-border/40">
          {/* Logo + título */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-7 h-7 rounded-btn bg-brand/15 flex items-center justify-center">
              <MapPin size={13} className="text-brand" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-[13px] font-semibold text-content-primary tracking-tight">
                UFI Barcelona
              </span>
              <span className="text-[10px] text-content-muted">
                Índice de Fricción Urbana
              </span>
            </div>
          </div>

          {/* Chip modo demo */}
          {degraded && (
            <div className="flex items-center gap-1.5 bg-amber-500/10 text-amber-400 text-[10px] font-medium px-2 py-1 rounded-chip border border-amber-500/20">
              <AlertTriangle size={10} />
              Demo
              <button
                onClick={() => setDegraded(false)}
                className="ml-0.5 hover:text-amber-200 transition-colors"
                aria-label="Cerrar aviso"
              >
                <X size={10} />
              </button>
            </div>
          )}

          <div className="flex-1" />

          {/* Chips de modo */}
          <div className="flex gap-1 shrink-0">
            {modes.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                aria-pressed={mode === m.id}
                className={`text-[10px] px-2.5 py-1 rounded-chip border transition-all duration-150 font-medium ${
                  mode === m.id
                    ? "bg-brand/15 text-brand border-brand/30"
                    : "bg-transparent text-content-muted border-surface-border hover:text-content-secondary hover:border-brand/20"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Toggle tramos */}
          <div className="flex items-center gap-2 shrink-0">
            <Layers
              size={12}
              className={showTramos ? "text-brand" : "text-content-muted"}
            />
            <span className="text-[10px] text-content-secondary">Tramos</span>
            <button
              role="switch"
              aria-checked={showTramos}
              aria-label="Mostrar tramos viarios"
              onClick={() => setShowTramos((v) => !v)}
              className={`relative w-8 h-4 rounded-chip transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 ${
                showTramos ? "bg-brand" : "bg-surface-3"
              }`}
            >
              <span
                className={`absolute top-0.5 w-3 h-3 rounded-full bg-content-primary shadow-sm transition-all duration-200 ${
                  showTramos ? "left-[18px]" : "left-0.5"
                }`}
              />
            </button>
          </div>

          {/* Spinner carga */}
          {loading && (
            <Loader2 size={14} className="text-brand/60 animate-spin shrink-0" />
          )}
        </div>

        {/* Row 2: Selector temporal */}
        <div className="flex items-center px-5 h-10">
          <TimeSlider />
        </div>
      </header>

      {/* ── Mapa fullscreen + sidebar flotante ─────────────────── */}
      <div className="flex-1 relative min-h-0 z-0">
        <MapView
          barrios={barriosGeo}
          ufiScores={ufiMap}
          tramosGeo={showTramos ? tramosGeo : null}
          tramoStates={showTramos ? tramoStates : undefined}
        />

        {/* Overlay carga */}
        {loading && (
          <div
            className="absolute inset-0 bg-surface-base/30 pointer-events-none z-10"
            aria-hidden="true"
          />
        )}

        {/* Sidebar flotante */}
        <aside className="absolute right-4 top-4 bottom-4 w-[300px] z-20 flex flex-col rounded-card bg-surface-2/85 backdrop-blur-glass border border-surface-border shadow-glass overflow-hidden animate-slide-in">

          {/* Sidebar header */}
          <div className="shrink-0 flex items-center justify-between px-4 py-3 border-b border-surface-border">
            {selectedBarrio ? (
              <>
                <button
                  onClick={() => selectBarrio(null)}
                  className="flex items-center gap-1.5 text-[11px] text-content-muted hover:text-content-primary transition-colors"
                >
                  <ArrowLeft size={12} />
                  Ranking
                </button>
                <span className="text-[9px] uppercase tracking-widest text-content-muted">
                  Detalle
                </span>
              </>
            ) : (
              <>
                <span className="text-[9px] font-semibold uppercase tracking-widest text-content-muted">
                  Top 10 · Peor fricción
                </span>
                {loading && (
                  <Loader2 size={11} className="text-brand/50 animate-spin" />
                )}
              </>
            )}
          </div>

          {/* Sidebar contenido */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {selectedBarrio ? (
              <BarrioPanel barrioId={selectedBarrio} at={at} mode={mode} />
            ) : loading ? (
              <SidebarSkeleton />
            ) : error ? (
              <EmptyState
                icon={<WifiOff size={18} />}
                title="Sin datos disponibles"
                message="Prueba otra franja horaria o comprueba la conexión"
              />
            ) : barrios.length === 0 ? (
              <EmptyState
                icon={<MousePointer2 size={18} />}
                title="Sin datos"
                message="No hay datos para este momento"
              />
            ) : (
              <ul className="py-1">
                {ranked.slice(0, 10).map((b) => {
                  const future = comp3h[b.barrio_id];
                  const delta = future !== undefined ? future - b.ufi : null;
                  const isSelected = selectedBarrio === b.barrio_id;
                  return (
                    <li
                      key={b.barrio_id}
                      role="button"
                      tabIndex={0}
                      aria-pressed={isSelected}
                      onClick={() => selectBarrio(isSelected ? null : b.barrio_id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          selectBarrio(isSelected ? null : b.barrio_id);
                        }
                      }}
                      className={`flex justify-between items-center px-4 py-2.5 cursor-pointer transition-colors outline-none focus-visible:bg-surface-3 ${
                        isSelected ? "bg-surface-3" : "hover:bg-surface-3/50"
                      }`}
                    >
                      <span className="text-[12px] text-content-secondary truncate flex-1">
                        {b.barrio_name}
                      </span>
                      <div className="flex items-center gap-1.5 ml-2 shrink-0">
                        {delta !== null && Math.abs(delta) >= 2 && (
                          <span
                            className={`text-[11px] font-bold leading-none ${
                              delta > 0 ? "text-red-400" : "text-teal-400"
                            }`}
                            title={`${delta > 0 ? "Empeora" : "Mejora"} ~${Math.abs(delta).toFixed(0)} pts en +3h`}
                          >
                            {delta > 0 ? "↑" : "↓"}
                          </span>
                        )}
                        <span
                          className={`font-mono text-[11px] px-1.5 py-0.5 rounded ${ufiChipClass(b.ufi)}`}
                        >
                          {b.ufi.toFixed(0)}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* Hint footer */}
          {!selectedBarrio && !loading && !error && barrios.length > 0 && (
            <div className="shrink-0 px-4 py-2.5 border-t border-surface-border">
              <p className="text-[10px] text-content-muted text-center">
                Haz clic en una zona del mapa para ver el detalle
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  message,
}: {
  icon: React.ReactNode;
  title: string;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-10 text-center">
      <div className="w-10 h-10 rounded-full bg-surface-3 flex items-center justify-center text-content-muted">
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-content-secondary mb-0.5">{title}</p>
        <p className="text-[11px] text-content-muted leading-relaxed">{message}</p>
      </div>
    </div>
  );
}

function SidebarSkeleton() {
  return (
    <div className="animate-pulse px-4 py-3 space-y-2.5">
      <div className="h-2 bg-surface-3 rounded w-1/3" />
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="h-2 bg-surface-3/60 rounded flex-1" />
          <div className="h-2 bg-surface-3/60 rounded w-8" />
        </div>
      ))}
    </div>
  );
}
