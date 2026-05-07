import { useEffect, useState } from "react";
import { api, type BarrioDetail, type ExplainResponse, type Mode } from "../api";
import { ufiTextClass } from "../utils/ufiColor";
import { Loader2, Info } from "lucide-react";
import ContribBar from "./ContribBar";

interface Props {
  barrioId: string;
  at: string | null;
  mode: Mode;
}

export default function BarrioPanel({ barrioId, at, mode }: Props) {
  const [detail, setDetail] = useState<BarrioDetail | null>(null);
  const [explain, setExplain] = useState<ExplainResponse | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(true);
  const [loadingExplain, setLoadingExplain] = useState(true);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setExplain(null);
    setErrorDetail(null);
    setLoadingDetail(true);
    setLoadingExplain(true);

    api
      .barrio(barrioId, at ?? undefined, mode)
      .then((d) => { if (!cancelled) setDetail(d); })
      .catch((e) => { if (!cancelled) { setErrorDetail("No disponible"); console.error(e); } })
      .finally(() => { if (!cancelled) setLoadingDetail(false); });

    api
      .explain(barrioId, at ?? undefined, mode)
      .then((e) => { if (!cancelled) setExplain(e); })
      .catch((e) => { if (!cancelled) console.error(e); })
      .finally(() => { if (!cancelled) setLoadingExplain(false); });

    return () => { cancelled = true; };
  }, [barrioId, at, mode]);

  if (loadingDetail) {
    return (
      <div className="flex items-center justify-center gap-2 py-10 text-content-muted">
        <Loader2 size={16} className="animate-spin" />
        <span className="text-xs">Cargando…</span>
      </div>
    );
  }

  if (errorDetail || !detail) {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center px-4">
        <p className="text-xs text-content-muted">No se pudo cargar el detalle.</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Score header */}
      <div className="px-4 pt-4 pb-3">
        <p className="text-[9px] uppercase tracking-widest text-content-muted mb-1">
          Índice de fricción
        </p>
        <div className="flex items-end justify-between gap-2">
          <h3 className="text-sm font-semibold text-content-primary leading-snug">
            {detail.barrio_name}
          </h3>
          <span
            className={`font-mono text-5xl font-bold tabular-nums leading-none shrink-0 ${ufiTextClass(detail.ufi)}`}
          >
            {detail.ufi.toFixed(0)}
          </span>
        </div>
        {/* UFI progress bar */}
        <div className="mt-3 h-1.5 bg-surface-3 rounded-chip overflow-hidden">
          <div
            className="h-full rounded-chip transition-all duration-700"
            style={{
              width: `${detail.ufi}%`,
              background:
                "linear-gradient(90deg, #2dd4bf 0%, #fbbf24 40%, #fb923c 70%, #f87171 100%)",
            }}
          />
        </div>
      </div>

      {/* Contributions */}
      <div className="px-4 py-3 border-t border-surface-border">
        <p className="text-[9px] uppercase tracking-widest text-content-muted mb-3">
          Contribución por factor
        </p>
        <ContribBar contributions={detail.contribuciones} />
      </div>

      {/* Explanation — solo visible si hay texto o está cargando */}
      {(loadingExplain || explain?.text) && (
        <div className="px-4 pb-5 border-t border-surface-border pt-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Info size={10} className="text-brand" />
            <p className="text-[9px] uppercase tracking-widest text-content-muted">
              Análisis
            </p>
          </div>
          <div className="rounded-lg bg-surface-3 px-3 py-3">
            {loadingExplain ? (
              <div className="flex items-center gap-2 text-xs text-content-muted">
                <Loader2 size={11} className="animate-spin shrink-0" />
                <span>Generando con Claude…</span>
              </div>
            ) : (
              <p className="text-[11px] text-content-secondary leading-relaxed">
                {explain!.text}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
