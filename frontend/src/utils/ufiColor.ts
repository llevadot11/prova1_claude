/** Convierte un score UFI 0–100 al RGBA usado por deck.gl */
export function ufiToColor(ufi: number): [number, number, number, number] {
  if (ufi < 30) return [45, 212, 191, 180];   // teal-400
  if (ufi < 60) return [251, 191, 36,  185];  // amber-400
  if (ufi < 80) return [251, 146, 60,  190];  // orange-400
  return          [248, 113, 113, 200];        // red-400
}

/** Clases Tailwind para chip de score en lista (fondo + texto) */
export function ufiChipClass(ufi: number): string {
  if (ufi < 30) return "bg-teal-500/15 text-teal-300 border border-teal-500/20";
  if (ufi < 60) return "bg-amber-500/15 text-amber-300 border border-amber-500/20";
  if (ufi < 80) return "bg-orange-500/15 text-orange-300 border border-orange-500/20";
  return               "bg-red-500/15 text-red-300 border border-red-500/20";
}

/** Clases Tailwind para el número de score grande */
export function ufiTextClass(ufi: number): string {
  if (ufi < 30) return "text-teal-400";
  if (ufi < 60) return "text-amber-400";
  if (ufi < 80) return "text-orange-400";
  return               "text-red-400";
}

export const UFI_LEGEND = [
  { label: "Fluido",   range: "0–29",  color: "#2dd4bf" },
  { label: "Moderado", range: "30–59", color: "#fbbf24" },
  { label: "Alto",     range: "60–79", color: "#fb923c" },
  { label: "Crítico",  range: "80+",   color: "#f87171" },
] as const;
