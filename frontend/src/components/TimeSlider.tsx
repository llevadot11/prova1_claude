import { useRef, useState } from "react";
import { useUFI } from "../store";

const QUICK_SLOTS = [
  { label: "Ahora", hours: 0  },
  { label: "+1h",   hours: 1  },
  { label: "+3h",   hours: 3  },
  { label: "+6h",   hours: 6  },
  { label: "+12h",  hours: 12 },
  { label: "+24h",  hours: 24 },
] as const;

export default function TimeSlider() {
  const { setAt } = useUFI();
  const [index, setIndex] = useState(0);
  const sessionStart = useRef(new Date());
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cuando el slider vuelve a 0 (Ahora), reancla sessionStart al momento actual
  // para que los siguientes "+Nh" sean relativos al nuevo "ahora"
  const handleReset = () => {
    sessionStart.current = new Date();
  };

  const applyIndex = (i: number) => {
    setIndex(i);
    if (i === 0) handleReset();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (i === 0) {
        setAt(null);
      } else {
        const d = new Date(sessionStart.current);
        d.setHours(d.getHours() + i);
        setAt(d.toISOString());
      }
    }, 150);
  };

  const activeHours = QUICK_SLOTS.find((s) => s.hours === index)?.hours ?? -1;

  const formattedTime =
    index > 0
      ? (() => {
          const d = new Date(sessionStart.current);
          d.setHours(d.getHours() + index);
          return d.toLocaleString("es-ES", {
            timeZone: "Europe/Madrid",
            weekday: "short",
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          });
        })()
      : null;

  return (
    <div className="flex items-center gap-3">
      {/* Quick chips */}
      <div className="flex gap-1">
        {QUICK_SLOTS.map((slot) => (
          <button
            key={slot.hours}
            onClick={() => applyIndex(slot.hours)}
            className={`text-[10px] px-2.5 py-1 rounded-chip border transition-all duration-150 font-medium ${
              activeHours === slot.hours
                ? "bg-brand/20 text-brand border-brand/40"
                : "bg-transparent text-content-muted border-surface-border hover:text-content-secondary hover:border-brand/30"
            }`}
          >
            {slot.label}
          </button>
        ))}
      </div>

      {/* Fine-grained slider */}
      <div className="flex flex-col items-center gap-0.5">
        <input
          type="range"
          min={0}
          max={47}
          step={1}
          value={index}
          onChange={(e) => applyIndex(Number(e.target.value))}
          aria-label="Seleccionar hora de predicción"
          aria-valuetext={index === 0 ? "Ahora" : `+${index} horas`}
          className="w-24"
        />
        <span className="text-[9px] text-content-muted tabular-nums h-3 leading-none">
          {formattedTime ?? ""}
        </span>
      </div>
    </div>
  );
}
