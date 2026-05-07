import { useMemo, useRef, useState } from "react";
import { useUFI } from "../store";

const QUICK_SLOTS = [
  { label: "Ahora", hours: 0 },
  { label: "+1h",   hours: 1 },
  { label: "+3h",   hours: 3 },
  { label: "+6h",   hours: 6 },
  { label: "+12h",  hours: 12 },
  { label: "+24h",  hours: 24 },
] as const;

const MAX_HOURS = 24;
const TICKS = [0, 3, 6, 9, 12, 15, 18, 21, 24];

export default function TimeSlider() {
  const setAt = useUFI((s) => s.setAt);
  const [index, setIndex] = useState(0);
  const sessionStart = useRef(new Date());
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const apply = (i: number) => {
    setIndex(i);
    if (i === 0) sessionStart.current = new Date();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (i === 0) {
        setAt(null);
      } else {
        const d = new Date(sessionStart.current);
        d.setHours(d.getHours() + i);
        setAt(d.toISOString());
      }
    }, 120);
  };

  const formatted = useMemo(() => {
    const d = new Date(sessionStart.current);
    if (index > 0) d.setHours(d.getHours() + index);
    return d.toLocaleString("es-ES", {
      timeZone: "Europe/Madrid",
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [index]);

  const pct = (index / MAX_HOURS) * 100;

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-caption uppercase text-ink-3">Hora prevista</span>
        <span className="font-mono text-mono text-ink tabular-nums">
          {formatted}
        </span>
      </div>

      <div className="relative w-full">
        <input
          type="range"
          min={0}
          max={MAX_HOURS}
          step={1}
          value={index}
          onChange={(e) => apply(Number(e.target.value))}
          aria-label="Seleccionar hora de predicción"
          aria-valuetext={index === 0 ? "Ahora" : `+${index} horas`}
          className="axis-scrubber"
        />
        <div className="absolute inset-x-0 top-[15px] h-3 flex justify-between pointer-events-none">
          {TICKS.map((t) => (
            <span
              key={t}
              aria-hidden="true"
              className={`w-px ${t === index ? "bg-accent-ink h-3" : "bg-rule h-2"}`}
              style={{ marginTop: t === index ? 0 : "4px" }}
            />
          ))}
        </div>
        <div
          aria-hidden="true"
          className="absolute -top-[2px] h-[2px] bg-accent-ink pointer-events-none transition-[width] duration-100"
          style={{ left: 0, width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between font-mono text-mono text-ink-3 tabular-nums">
        {TICKS.map((t) => (
          <span key={t} className={t === index ? "text-ink" : ""}>
            {t === 0 ? "ahora" : `+${t}h`}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-body-sm pt-1">
        {QUICK_SLOTS.map((slot) => {
          const active = index === slot.hours;
          return (
            <button
              key={slot.hours}
              type="button"
              onClick={() => apply(slot.hours)}
              aria-pressed={active}
              className={`relative pb-px transition-colors duration-100 ${
                active
                  ? "text-ink font-semibold"
                  : "text-ink-3 hover:text-ink-2"
              }`}
            >
              {slot.label}
              {active && (
                <span
                  aria-hidden="true"
                  className="absolute left-0 right-0 -bottom-px h-[2px] bg-accent-ink"
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
