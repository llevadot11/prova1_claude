import { useState } from "react";
import type { Mode } from "../api";

interface ModeOption {
  id: Mode;
  label: string;
  description?: string;
}

interface Props {
  modes: ModeOption[];
  active: Mode;
  onChange: (m: Mode) => void;
}

export default function ModeRegister({ modes, active, onChange }: Props) {
  if (modes.length === 0) return null;

  return (
    <>
      <div className="hidden md:flex items-stretch text-body-sm">
        {modes.map((m, i) => {
          const isActive = m.id === active;
          return (
            <div key={m.id} className="flex items-stretch">
              {i > 0 && (
                <span aria-hidden="true" className="self-stretch w-px bg-rule mx-3" />
              )}
              <button
                type="button"
                onClick={() => onChange(m.id)}
                aria-pressed={isActive}
                title={m.description}
                className={`relative inline-flex items-center pb-1 transition-colors duration-150 ${
                  isActive
                    ? "text-ink font-semibold"
                    : "text-ink-3 hover:text-ink-2 font-normal"
                }`}
              >
                {m.label}
                <span
                  aria-hidden="true"
                  className={`absolute left-0 right-0 -bottom-px h-[2px] bg-accent-ink transition-opacity ${
                    isActive ? "opacity-100" : "opacity-0"
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>

      <ModeDropdown modes={modes} active={active} onChange={onChange} />
    </>
  );
}

function ModeDropdown({ modes, active, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const current = modes.find((m) => m.id === active) ?? modes[0];

  return (
    <div className="md:hidden relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-baseline gap-2 text-body-sm text-ink"
      >
        <span className="text-caption uppercase text-ink-3">Modo</span>
        <span className="font-semibold">{current.label}</span>
        <span aria-hidden="true" className="text-ink-3 text-[10px]">▾</span>
      </button>
      {open && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <ul
            role="listbox"
            className="absolute top-full right-0 mt-2 z-40 min-w-[180px] bg-paper border border-rule"
          >
            {modes.map((m) => (
              <li key={m.id}>
                <button
                  role="option"
                  aria-selected={m.id === active}
                  onClick={() => {
                    onChange(m.id);
                    setOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-body-sm border-b border-rule last:border-b-0 ${
                    m.id === active
                      ? "text-ink font-semibold bg-paper-2"
                      : "text-ink-2 hover:bg-paper-2"
                  }`}
                >
                  {m.label}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
