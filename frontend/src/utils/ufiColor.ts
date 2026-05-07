// Earthy, pigment-printed UFI ramp. OKLCH spec → precomputed sRGB for deck.gl + CSS.
// Six stops align with the legend. Keep RGB and HEX in sync if either is tuned.

export interface UFIStop {
  range: string;
  label: string;
  rgb: [number, number, number];
  hex: string;
}

export const UFI_STOPS: readonly UFIStop[] = [
  { range: "0–14",   label: "Fluido",    rgb: [178, 219, 200], hex: "#b2dbc8" },
  { range: "15–29",  label: "Bajo",      rgb: [155, 198, 167], hex: "#9bc6a7" },
  { range: "30–44",  label: "Moderado",  rgb: [220, 198, 130], hex: "#dcc682" },
  { range: "45–59",  label: "Alto",      rgb: [212, 154,  79], hex: "#d49a4f" },
  { range: "60–74",  label: "Muy alto",  rgb: [196, 102,  60], hex: "#c4663c" },
  { range: "75–100", label: "Crítico",   rgb: [150,  56,  35], hex: "#963823" },
] as const;

function bucket(ufi: number): number {
  if (ufi < 15) return 0;
  if (ufi < 30) return 1;
  if (ufi < 45) return 2;
  if (ufi < 60) return 3;
  if (ufi < 75) return 4;
  return 5;
}

export function ufiStop(ufi: number): UFIStop {
  return UFI_STOPS[bucket(ufi)];
}

export function ufiHex(ufi: number): string {
  return UFI_STOPS[bucket(ufi)].hex;
}

export function ufiQualifier(ufi: number): string {
  return UFI_STOPS[bucket(ufi)].label;
}

export function ufiToColor(ufi: number): [number, number, number, number] {
  const [r, g, b] = UFI_STOPS[bucket(ufi)].rgb;
  return [r, g, b, 190];
}

export const UFI_LEGEND = UFI_STOPS;
