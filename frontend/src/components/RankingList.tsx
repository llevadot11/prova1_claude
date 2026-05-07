import type { BarrioUFI } from "../api";
import { ufiHex } from "../utils/ufiColor";

interface Props {
  barrios: BarrioUFI[];
  forecast3h?: Record<string, number>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function RankingList({
  barrios,
  forecast3h,
  selectedId,
  onSelect,
}: Props) {
  if (barrios.length === 0) {
    return (
      <p className="px-5 py-6 text-body-sm text-ink-3">
        Sin datos para esta franja horaria.
      </p>
    );
  }

  const ranked = [...barrios].sort((a, b) => b.ufi - a.ufi).slice(0, 10);

  return (
    <ol className="border-t border-rule">
      {ranked.map((b, i) => {
        const future = forecast3h?.[b.barrio_id];
        const delta = future !== undefined ? future - b.ufi : null;
        const isSelected = selectedId === b.barrio_id;
        return (
          <li key={b.barrio_id} className="border-b border-rule last:border-b-0">
            <button
              type="button"
              onClick={() => onSelect(b.barrio_id)}
              aria-pressed={isSelected}
              className={`group w-full grid grid-cols-[28px_1fr_auto] items-baseline gap-3 py-3 pr-5 text-left transition-colors duration-100 outline-none ${
                isSelected
                  ? "bg-paper-2 pl-[18px] border-l-2 border-accent-ink"
                  : "pl-5 hover:bg-paper-2 border-l-2 border-transparent"
              }`}
            >
              <span className="font-mono text-mono text-ink-3 tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="text-body text-ink leading-snug truncate">
                {b.barrio_name}
              </span>
              <span className="flex items-baseline gap-2 shrink-0">
                {delta !== null && Math.abs(delta) >= 2 && (
                  <span
                    className="text-mono font-mono tabular-nums text-ink-3"
                    title={`${delta > 0 ? "Empeora" : "Mejora"} ~${Math.abs(delta).toFixed(0)} pts en +3h`}
                  >
                    {delta > 0 ? "▲" : "▼"}
                    {Math.abs(delta).toFixed(0)}
                  </span>
                )}
                <span
                  className="font-mono text-mono-lg font-medium tabular-nums"
                  style={{ color: ufiHex(b.ufi) }}
                >
                  {b.ufi.toFixed(0)}
                </span>
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
