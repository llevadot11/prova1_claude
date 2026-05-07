import { useEffect, useMemo, useRef, useState } from "react";
import type { FeatureCollection } from "geojson";
import { api, type BarrioUFI, type ModePreset } from "./api";
import { useUFI } from "./store";
import MapView from "./components/MapView";
import TimeSlider from "./components/TimeSlider";
import BarrioPanel from "./components/BarrioPanel";
import ModeRegister from "./components/ModeRegister";
import RankingList from "./components/RankingList";

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

  const [sheetOpen, setSheetOpen] = useState(false);

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

  useEffect(() => {
    if (selectedBarrio) setSheetOpen(true);
  }, [selectedBarrio]);

  const ufiMap = useMemo(
    () => Object.fromEntries(barrios.map((b) => [b.barrio_id, b])),
    [barrios]
  );

  return (
    <div className="flex flex-col h-full bg-paper text-ink">
      <Masthead
        modes={modes}
        mode={mode}
        onModeChange={setMode}
        showTramos={showTramos}
        onToggleTramos={() => setShowTramos((v) => !v)}
        loading={loading}
        degraded={degraded}
        onDismissDegraded={() => setDegraded(false)}
      />

      <main className="flex-1 relative min-h-0 grid grid-cols-1 lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_400px]">
        <section className="relative min-h-0 flex flex-col border-t border-rule lg:border-r">
          <div className="relative flex-1 min-h-0">
            <MapView
              barrios={barriosGeo}
              ufiScores={ufiMap}
              tramosGeo={showTramos ? tramosGeo : null}
              tramoStates={showTramos ? tramoStates : undefined}
            />
            {loading && (
              <div
                className="absolute inset-0 bg-paper/20 pointer-events-none z-10"
                aria-hidden="true"
              />
            )}
          </div>
          <SourcesBar />
        </section>

        <aside className="hidden lg:flex flex-col bg-paper-2 border-t border-rule overflow-hidden">
          <ColumnContent
            selectedBarrio={selectedBarrio}
            onSelectBarrio={selectBarrio}
            at={at}
            mode={mode}
            barrios={barrios}
            comp3h={comp3h}
            error={error}
            loading={loading}
          />
        </aside>

        <MobileSheet
          open={sheetOpen}
          onClose={() => {
            setSheetOpen(false);
            selectBarrio(null);
          }}
          onOpen={() => setSheetOpen(true)}
        >
          <ColumnContent
            selectedBarrio={selectedBarrio}
            onSelectBarrio={selectBarrio}
            at={at}
            mode={mode}
            barrios={barrios}
            comp3h={comp3h}
            error={error}
            loading={loading}
          />
        </MobileSheet>
      </main>
    </div>
  );
}

function SourcesBar() {
  return (
    <div className="shrink-0 bg-paper border-t border-rule px-6 md:px-8 py-2 hidden md:flex items-baseline justify-between gap-6 text-caption uppercase tracking-[0.04em] text-ink-3 select-none">
      <span>
        fuentes: open-meteo · ajuntament de barcelona · openstreetmap · datos públicos
      </span>
      <span className="font-mono tabular-nums">
        v0.1 · build 2026-05
      </span>
    </div>
  );
}

interface MastheadProps {
  modes: ModePreset[];
  mode: ModePreset["id"];
  onModeChange: (m: ModePreset["id"]) => void;
  showTramos: boolean;
  onToggleTramos: () => void;
  loading: boolean;
  degraded: boolean | null;
  onDismissDegraded: () => void;
}

function Masthead({
  modes,
  mode,
  onModeChange,
  showTramos,
  onToggleTramos,
  loading,
  degraded,
  onDismissDegraded,
}: MastheadProps) {
  return (
    <header className="shrink-0 bg-paper-2 border-b-2 border-rule-strong z-20">
      {/* Eyebrow row — numbered editorial title-card */}
      <div className="px-4 md:px-8 pt-2.5 md:pt-3.5 pb-1 flex items-baseline justify-between gap-3">
        <p className="font-mono text-[10px] md:text-[11px] uppercase tracking-[0.06em] text-ink-3 truncate">
          <span className="tabular-nums text-ink-2">01</span>
          <span className="mx-2">—</span>
          <span className="hidden sm:inline">diagnóstico urbano de barcelona, en directo</span>
          <span className="sm:hidden">diagnóstico bcn, en directo</span>
        </p>
        <div className="hidden md:flex items-baseline gap-5 shrink-0">
          {loading && !degraded && (
            <span className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-3 tabular-nums">
              cargando…
            </span>
          )}
          {degraded && <DemoNotice onDismiss={onDismissDegraded} />}
        </div>
      </div>

      {/* Wordmark + mode register + tramos */}
      <div className="px-4 md:px-8 pb-2 md:pb-3 flex items-end justify-between gap-4 flex-wrap">
        <h1 className="font-display text-[28px] md:text-[44px] leading-[0.95] text-ink whitespace-nowrap">
          UFI <span className="italic">Barcelona</span>
        </h1>
        <div className="flex items-baseline gap-4 md:gap-6 ml-auto">
          <ModeRegister modes={modes} active={mode} onChange={onModeChange} />
          <button
            type="button"
            onClick={onToggleTramos}
            aria-pressed={showTramos}
            className={`hidden md:inline-flex items-baseline gap-1 text-body-sm transition-colors duration-150 ${
              showTramos
                ? "text-ink font-semibold underline underline-offset-[6px] decoration-2 decoration-accent-ink"
                : "text-ink-3 hover:text-ink-2"
            }`}
          >
            tramos viarios
            <span aria-hidden="true" className="font-mono">→</span>
          </button>
          <button
            type="button"
            onClick={onToggleTramos}
            aria-pressed={showTramos}
            className={`md:hidden text-body-sm ${
              showTramos ? "text-ink font-semibold" : "text-ink-3"
            }`}
          >
            tramos →
          </button>
        </div>
      </div>

      {/* Time scrubber — hidden on mobile portrait, lives in sheet header instead */}
      <div className="px-4 md:px-8 py-2 md:py-2.5 border-t border-rule">
        <TimeSlider />
      </div>
    </header>
  );
}

function DemoNotice({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="flex items-baseline gap-2 pl-3 border-l-2" style={{ borderColor: "#d49a4f" }}>
      <span className="font-mono text-mono text-ink-2 tabular-nums">
        modo demo
      </span>
      <span className="text-body-sm text-ink-3">datos cacheados</span>
      <button
        onClick={onDismiss}
        className="text-mono font-mono text-ink-3 hover:text-ink ml-1"
        aria-label="Cerrar aviso"
      >
        ×
      </button>
    </div>
  );
}

interface ColumnContentProps {
  selectedBarrio: string | null;
  onSelectBarrio: (id: string | null) => void;
  at: string | null;
  mode: ModePreset["id"];
  barrios: BarrioUFI[];
  comp3h: Record<string, number>;
  error: string | null;
  loading: boolean;
}

function ColumnContent({
  selectedBarrio,
  onSelectBarrio,
  at,
  mode,
  barrios,
  comp3h,
  error,
  loading,
}: ColumnContentProps) {
  if (selectedBarrio) {
    return (
      <>
        <div className="shrink-0 px-5 py-3 border-b border-rule flex items-baseline justify-between">
          <button
            type="button"
            onClick={() => onSelectBarrio(null)}
            className="text-body-sm text-ink-3 hover:text-ink transition-colors"
          >
            <span aria-hidden="true">←</span> volver al ranking
          </button>
          <span className="font-mono text-caption uppercase tracking-[0.06em] text-ink-2 tabular-nums">
            [02] detalle
          </span>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0">
          <BarrioPanel barrioId={selectedBarrio} at={at} mode={mode} />
        </div>
      </>
    );
  }

  return (
    <>
      <div className="shrink-0 px-5 pt-4 pb-3">
        <p className="font-mono text-caption uppercase tracking-[0.06em] text-ink-2 tabular-nums mb-1.5">
          [01] ranking
        </p>
        <h2 className="font-display text-display-lg italic text-ink leading-tight">
          ¿Qué evitar ahora mismo?
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {loading && barrios.length === 0 ? (
          <RankingSkeleton />
        ) : error ? (
          <p className="px-5 py-6 text-body-sm text-ink-3">
            Sin datos disponibles. Prueba otra franja horaria.
          </p>
        ) : (
          <RankingList
            barrios={barrios}
            forecast3h={comp3h}
            selectedId={selectedBarrio}
            onSelect={onSelectBarrio}
          />
        )}
      </div>

      <div className="shrink-0 px-5 py-3 border-t border-rule">
        <p className="text-caption text-ink-3 leading-relaxed">
          Selecciona un barri en el mapa o en la lista para leer la diagnosis completa.
        </p>
      </div>
    </>
  );
}

function RankingSkeleton() {
  return (
    <ul className="border-t border-rule">
      {Array.from({ length: 10 }).map((_, i) => (
        <li key={i} className="border-b border-rule px-5 py-3.5 flex items-baseline gap-3">
          <span className="font-mono text-mono text-ink-3 tabular-nums">
            {String(i + 1).padStart(2, "0")}
          </span>
          <span className="flex-1 h-3 bg-paper-3" />
          <span className="font-mono text-mono text-paper-3 tabular-nums">––</span>
        </li>
      ))}
    </ul>
  );
}

interface MobileSheetProps {
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  children: React.ReactNode;
}

function MobileSheet({ open, onOpen, onClose, children }: MobileSheetProps) {
  return (
    <div
      className={`lg:hidden fixed inset-x-0 bottom-0 z-30 bg-paper-2 border-t-2 border-rule-strong transition-transform duration-200 ease-out ${
        open ? "translate-y-0" : "translate-y-[calc(100%-48px)]"
      }`}
      style={{ maxHeight: "62vh", height: "62vh" }}
    >
      <button
        type="button"
        onClick={open ? onClose : onOpen}
        className="w-full px-4 py-2.5 flex items-center justify-between border-b border-rule"
        aria-expanded={open}
      >
        <span className="font-mono text-caption uppercase tracking-[0.06em] text-ink-2 tabular-nums">
          {open ? "[×] cerrar" : "[01] ranking · ver"}
        </span>
        <span className="font-mono text-mono text-ink tabular-nums">
          {open ? "▾" : "▴"}
        </span>
      </button>
      <div className="flex flex-col h-[calc(100%-41px)] overflow-hidden">
        {children}
      </div>
    </div>
  );
}
