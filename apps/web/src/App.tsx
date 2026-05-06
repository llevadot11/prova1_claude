import { useEffect, useState } from "react";
import { api, type BarrioUFI, type ModePreset } from "./api";
import { useUFI } from "./store";

export default function App() {
  const { mode, setMode, selectedBarrio, selectBarrio } = useUFI();
  const [barrios, setBarrios] = useState<BarrioUFI[]>([]);
  const [modes, setModes] = useState<ModePreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.ufi(undefined, mode), api.modes()])
      .then(([ufi, presets]) => {
        setBarrios(ufi.barrios);
        setModes(presets);
        setError(null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [mode]);

  const ranked = [...barrios].sort((a, b) => b.ufi - a.ufi);
  const selected = barrios.find((b) => b.barrio_id === selectedBarrio);

  return (
    <div className="flex h-full">
      {/* Mapa placeholder — Persona A reemplaza con MapLibre + deck.gl */}
      <div className="flex-1 bg-slate-100 grid place-items-center text-slate-500 text-sm">
        [Mapa MapLibre + deck.gl pendiente]
      </div>

      <aside className="w-96 border-l border-slate-200 p-4 overflow-y-auto">
        <h1 className="text-xl font-bold mb-1">UFI Barcelona</h1>
        <p className="text-xs text-slate-500 mb-4">
          ¿Qué zonas estarán peor para moverse? Modo actual:{" "}
          <span className="font-semibold">{mode}</span>
        </p>

        <div className="flex flex-wrap gap-1 mb-4">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`text-xs px-2 py-1 rounded border ${
                mode === m.id
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white border-slate-300"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {loading && <div className="text-slate-400 text-sm">Cargando…</div>}
        {error && <div className="text-red-600 text-sm">{error}</div>}

        {!loading && !error && (
          <>
            <h2 className="text-sm font-semibold mb-2">Top 10 peor UFI</h2>
            <ul className="text-sm">
              {ranked.slice(0, 10).map((b) => (
                <li
                  key={b.barrio_id}
                  onClick={() => selectBarrio(b.barrio_id)}
                  className={`flex justify-between py-1 cursor-pointer ${
                    selected?.barrio_id === b.barrio_id ? "bg-slate-100" : ""
                  }`}
                >
                  <span>{b.barrio_name}</span>
                  <span className="font-mono">{b.ufi.toFixed(0)}</span>
                </li>
              ))}
            </ul>

            {selected && (
              <div className="mt-6 border-t border-slate-200 pt-4">
                <h3 className="font-semibold">{selected.barrio_name}</h3>
                <p className="text-2xl font-bold">{selected.ufi.toFixed(0)}</p>
                <ul className="mt-2 text-xs">
                  {selected.contribuciones
                    .sort((a, b) => b.contribution_pct - a.contribution_pct)
                    .map((c) => (
                      <li key={c.family} className="flex justify-between">
                        <span>{c.family}</span>
                        <span className="font-mono">
                          {c.contribution_pct.toFixed(0)}%
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
