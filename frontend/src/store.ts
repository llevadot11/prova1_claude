import { create } from "zustand";
import type { Mode } from "./api";

interface UFIStore {
  mode: Mode;
  at: string | null;
  selectedBarrio: string | null;
  setMode: (m: Mode) => void;
  setAt: (at: string | null) => void;
  selectBarrio: (id: string | null) => void;
}

export const useUFI = create<UFIStore>((set) => ({
  mode: "default",
  at: null,
  selectedBarrio: null,
  setMode: (mode) => set({ mode }),
  setAt: (at) => set({ at }),
  selectBarrio: (id) => set({ selectedBarrio: id }),
}));
