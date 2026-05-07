import { useEffect, useState } from "react";
import { api, type BarrioDetail, type ExplainResponse, type Mode } from "../api";
import { ufiHex, ufiQualifier } from "../utils/ufiColor";
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
      <div className="px-5 py-8">
        <p className="font-mono text-mono text-ink-3 tabular-nums">
          Cargando barri…
        </p>
      </div>
    );
  }

  if (errorDetail || !detail) {
    return (
      <div className="px-5 py-8">
        <p className="text-body-sm text-ink-3">
          No se pudo cargar el detalle del barri.
        </p>
      </div>
    );
  }

  const at_iso = detail.at;
  const formatted = new Date(at_iso).toLocaleString("es-ES", {
    timeZone: "Europe/Madrid",
    weekday: "long",
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <article className="ufi-fade-up">
      <header className="px-5 pt-5 pb-4 border-b border-rule">
        {detail.district_name && (
          <p className="font-mono text-caption uppercase tracking-[0.06em] text-ink-3 mb-1 lowercase">
            {detail.district_name}
          </p>
        )}
        <h2 className="font-display text-display-xl italic text-ink leading-[1.05] mb-3">
          {detail.barrio_name}
        </h2>
        <div className="flex items-baseline gap-3">
          <span
            className="font-mono text-[44px] leading-none font-medium tabular-nums"
            style={{ color: ufiHex(detail.ufi) }}
          >
            {detail.ufi.toFixed(0)}
          </span>
          <span className="text-body-sm text-ink-2">
            <span className="font-medium">{ufiQualifier(detail.ufi).toLowerCase()}</span>
            <span className="text-ink-3"> · ufi 0–100</span>
          </span>
        </div>
      </header>

      <section className="px-5 py-4 border-b border-rule">
        <h3 className="font-mono text-caption uppercase tracking-[0.06em] text-ink-2 mb-3 tabular-nums">
          [a] contribución por factor
        </h3>
        <ContribBar contributions={detail.contribuciones} />
      </section>

      {(loadingExplain || explain?.text) && (
        <section className="px-5 py-4 border-b border-rule">
          <h3 className="font-mono text-caption uppercase tracking-[0.06em] text-ink-2 mb-2 tabular-nums">
            [b] lectura de la zona
          </h3>
          {loadingExplain ? (
            <p className="font-mono text-mono text-ink-3 tabular-nums">
              generando lectura…
            </p>
          ) : (
            <p className="font-display text-body-lg text-ink leading-[1.55]">
              {explain!.text}
            </p>
          )}
        </section>
      )}

      <footer className="px-5 py-3 text-caption text-ink-3 leading-snug">
        calculado para <span className="text-ink-2">{formatted}</span>
        <span className="mx-1.5 text-ink-3">·</span>
        modo <span className="text-ink-2">{detail.mode}</span>
      </footer>
    </article>
  );
}
