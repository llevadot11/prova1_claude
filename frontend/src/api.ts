// Cliente API tipado contra apps/api. Refleja apps/api/app/schemas.py.
// Persona B y A se sincronizan en este fichero — si rompe el contrato, romper aquí también.

const BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export type Mode = "default" | "familiar" | "runner" | "movilidad_reducida";
export type Family = "trafico" | "accidentes" | "aire" | "meteo" | "sensibilidad";

export interface FamilyContribution {
  family: Family;
  score: number;
  weight: number;
  contribution_pct: number;
}

export interface BarrioUFI {
  barrio_id: string;
  barrio_name: string;
  ufi: number;
  contribuciones: FamilyContribution[];
}

export interface UFIResponse {
  at: string;
  mode: Mode;
  barrios: BarrioUFI[];
}

export interface TramoState {
  tram_id: number;
  state: number;
}

export interface TramosStateResponse {
  at: string;
  tramos: TramoState[];
}

export interface BarrioDetail {
  barrio_id: string;
  barrio_name: string;
  at: string;
  mode: Mode;
  ufi: number;
  contribuciones: FamilyContribution[];
  raw: Record<string, number | string | null>;
}

export interface ExplainResponse {
  barrio_id: string;
  at: string;
  mode: Mode;
  text: string;
  cached: boolean;
}

export interface ModePreset {
  id: Mode;
  label: string;
  description: string;
  weights: Record<Family, number>;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return (await r.json()) as T;
}

export const api = {
  barrios: () => get<GeoJSON.FeatureCollection>("/barrios"),
  tramos: () => get<GeoJSON.FeatureCollection>("/tramos"),
  ufi: (at?: string, mode: Mode = "default") =>
    get<UFIResponse>(`/ufi?${new URLSearchParams({ ...(at && { at }), mode })}`),
  tramosState: (at?: string) =>
    get<TramosStateResponse>(`/tramos/state${at ? `?at=${at}` : ""}`),
  barrio: (id: string, at?: string, mode: Mode = "default") =>
    get<BarrioDetail>(`/barrio/${id}?${new URLSearchParams({ ...(at && { at }), mode })}`),
  explain: (id: string, at?: string, mode: Mode = "default") =>
    get<ExplainResponse>(`/explain/${id}?${new URLSearchParams({ ...(at && { at }), mode })}`),
  modes: () => get<ModePreset[]>("/modes"),
  health: () => get<Record<string, unknown>>("/health"),
};
