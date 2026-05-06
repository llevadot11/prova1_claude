import { Car, Wind, Cloud, AlertTriangle, Activity, type LucideIcon } from "lucide-react";
import type { Family, FamilyContribution } from "../api";

const FAMILY_CONFIG: Record<
  Family,
  { label: string; icon: LucideIcon; barColor: string; iconColor: string }
> = {
  trafico:      { label: "Tráfico",          icon: Car,           barColor: "bg-blue-500",   iconColor: "text-blue-400"   },
  aire:         { label: "Calidad del aire",  icon: Wind,          barColor: "bg-teal-500",   iconColor: "text-teal-400"   },
  meteo:        { label: "Meteorología",      icon: Cloud,         barColor: "bg-cyan-500",   iconColor: "text-cyan-400"   },
  accidentes:   { label: "Accidentes",        icon: AlertTriangle, barColor: "bg-orange-500", iconColor: "text-orange-400" },
  sensibilidad: { label: "Sensibilidad",      icon: Activity,      barColor: "bg-purple-500", iconColor: "text-purple-400" },
};

interface Props {
  contributions: FamilyContribution[];
}

export default function ContribBar({ contributions }: Props) {
  const sorted = [...contributions].sort(
    (a, b) => b.contribution_pct - a.contribution_pct
  );

  return (
    <ul className="space-y-3">
      {sorted.map((c) => {
        const cfg = FAMILY_CONFIG[c.family];
        if (!cfg) return null;
        const { label, icon: Icon, barColor, iconColor } = cfg;
        return (
          <li key={c.family}>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5">
                <Icon size={11} className={iconColor} />
                <span className="text-[11px] text-content-secondary">{label}</span>
              </div>
              <span className="text-[11px] font-mono font-medium text-content-primary tabular-nums">
                {c.contribution_pct.toFixed(0)}%
              </span>
            </div>
            <div className="h-1.5 bg-surface-3 rounded-chip overflow-hidden">
              <div
                className={`h-full rounded-chip transition-all duration-500 ${barColor}`}
                style={{
                  width: `${c.contribution_pct}%`,
                  minWidth: c.contribution_pct > 0 ? "4px" : "0",
                }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
