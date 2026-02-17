import { create } from "zustand";
import type { TcgaPreset, RuntimeInfo } from "@/types/analysis";

interface ConfigState {
  runtime: RuntimeInfo;
  presets: TcgaPreset[];
  runtimeChecked: boolean;
  rPathOverride: string;
  pixiPathOverride: string;

  setRuntimeInfo: (info: RuntimeInfo) => void;
  setPresets: (presets: TcgaPreset[]) => void;
  setRPathOverride: (path: string) => void;
  setPixiPathOverride: (path: string) => void;
}

export const useConfigStore = create<ConfigState>()((set) => ({
  runtime: { rPath: null, pixiPath: null, rVersion: null },
  presets: [],
  runtimeChecked: false,
  rPathOverride: "",
  pixiPathOverride: "",

  setRuntimeInfo: (info) => set({ runtime: info, runtimeChecked: true }),
  setPresets: (presets) => set({ presets }),
  setRPathOverride: (path) => set({ rPathOverride: path }),
  setPixiPathOverride: (path) => set({ pixiPathOverride: path }),
}));
