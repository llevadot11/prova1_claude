import { UFI_STOPS } from "../utils/ufiColor";

export default function Legend() {
  return (
    <div className="select-none pointer-events-none">
      <p className="text-caption uppercase font-medium text-ink-3 mb-2">
        Índice UFI
      </p>
      <ul className="flex flex-col gap-[5px]">
        {UFI_STOPS.map((stop) => (
          <li key={stop.range} className="flex items-center gap-2.5">
            <span
              className="block h-[6px] w-6 shrink-0"
              style={{ backgroundColor: stop.hex }}
              aria-hidden="true"
            />
            <span className="font-mono text-mono text-ink-2 tabular-nums w-14">
              {stop.range}
            </span>
            <span className="text-body-sm text-ink-2">{stop.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
