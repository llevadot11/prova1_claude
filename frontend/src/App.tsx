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
        <section className="relative min-h-0 border-t border-rule lg:border-r">
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
      <div className="px-6 md:px-8 pt-5 md:pt-6 pb-4">
        <div className="flex items-start justify-between gap-6">
          <div className="min-w-0">
            <h1 className="font-display text-[40px] md:text-display-2xl leading-[0.95] text-ink">
              UFI <span className="italic">Barcelona</span>
            </h1>
            <p className="mt-1 text-body-sm text-ink-2">
              Índice de Fricción Urbana
              <span className="text-ink-3"> · diagnóstico por barri y franja horaria</span>
            </p>
          </div>
          <div className="hidden md:flex flex-col items-end gap-2 shrink-0">
            <button
              type="button"
              onClick={onToggleTramos}
              aria-pressed={showTramos}
              className={`text-body-sm transition-colors duration-150 ${
                showTramos ? "text-ink font-semibold" : "text-ink-3 hover:text-ink-2"
              }`}
            >
              <span className="font-mono text-mono mr-2 tabular-nums">
                {showTramos ? "[×]" : "[ ]"}
              </span>
              Tramos viarios
            </button>
            {degraded && (
              <DemoNotice onDismiss={onDismissDegraded} />
            )}
            {loading && !degraded && (
              <span className="font-mono text-mono text-ink-3 tabular-nums">
                cargando…
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 md:px-8 py-3 border-t border-rule flex flex-wrap items-center gap-x-6 gap-y-3">
        <ModeRegister modes={modes} active={mode} onChange={onModeChange} />
        <button
          type="button"
          onClick={onToggleTramos}
          aria-pressed={showTramos}
          className={`md:hidden text-body-sm ${
            showTramos ? "text-ink font-semibold" : "text-ink-3"
          }`}
        >
          <span className="font-mono text-mono mr-1.5 tabular-nums">
            {showTramos ? "[×]" : "[ ]"}
          </span>
          Tramos
        </button>
      </div>

      <div className="px-6 md:px-8 py-4 border-t border-rule">
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
            ← Volver al ranking
          </button>
          <span className="text-caption uppercase text-ink-3">Detalle</span>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0">
          <BarrioPanel barrioId={selectedBarrio} at={at} mode={mode} />
        </div>
      </>
    );
  }

  return (
    <>
      <div className="shrink-0 px-5 py-4">
        <p className="text-caption uppercase text-ink-3 mb-1">
          Top 10 — peor fricción
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
        open ? "translate-y-0" : "translate-y-[calc(100%-56px)]"
      }`}
      style={{ maxHeight: "82vh", height: "82vh" }}
    >
      <button
        type="button"
        onClick={open ? onClose : onOpen}
        className="w-full px-5 py-3 flex items-center justify-between border-b border-rule"
        aria-expanded={open}
      >
        <span className="text-caption uppercase text-ink-3">
          {open ? "Cerrar" : "Top 10 / detalle"}
        </span>
        <span className="font-mono text-mono text-ink tabular-nums">
          {open ? "▾" : "▴"}
        </span>
      </button>
      <div className="flex flex-col h-[calc(100%-49px)] overflow-hidden">
        {children}
      </div>
    </div>
  );
}
