import type { Family, FamilyContribution } from "../api";

const FAMILY_LABEL: Record<Family, string> = {
  trafico:      "Tráfico",
  aire:         "Calidad del aire",
  meteo:        "Meteorología",
  accidentes:   "Accidentes",
  sensibilidad: "Sensibilidad",
};

const FAMILY_HEX: Record<Family, string> = {
  trafico:      "#c4663c",
  accidentes:   "#963823",
  aire:         "#9bc6a7",
  meteo:        "#d49a4f",
  sensibilidad: "#5a6b8c",
};

interface Props {
  contributions: FamilyContribution[];
}

export default function ContribBar({ contributions }: Props) {
  const sorted = [...contributions].sort(
    (a, b) => b.contribution_pct - a.contribution_pct
  );

  return (
    <ul className="flex flex-col gap-3">
      {sorted.map((c) => {
        const label = FAMILY_LABEL[c.family];
        const color = FAMILY_HEX[c.family];
        if (!label) return null;
        const pct = Math.max(0, Math.min(100, c.contribution_pct));
        return (
          <li key={c.family} className="grid grid-cols-[1fr_auto] gap-x-3 items-baseline">
            <span className="text-body-sm text-ink-2">{label}</span>
            <span className="font-mono text-mono text-ink tabular-nums">
              {pct.toFixed(0)}%
            </span>
            <div
              className="col-span-2 h-[6px] bg-paper-3"
              role="presentation"
            >
              <div
                className="h-full transition-[width] duration-300 ease-out-quart"
                style={{
                  width: `${pct}%`,
                  backgroundColor: color,
                  minWidth: pct > 0 ? "2px" : 0,
                }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
