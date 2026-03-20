import { create } from 'zustand';
import type { MapLayerId } from '@/types';

interface Viewport {
  latitude: number;
  longitude: number;
  zoom: number;
}

interface MapState {
  viewport: Viewport;
  activeLayers: MapLayerId[];
  selectedDistrict: string | null;
  yearRange: [number, number];
  setViewport: (viewport: Partial<Viewport>) => void;
  toggleLayer: (layer: MapLayerId) => void;
  setSelectedDistrict: (pcode: string | null) => void;
  setYearRange: (range: [number, number]) => void;
}

export const useMapStore = create<MapState>((set) => ({
  viewport: {
    latitude: 30.3753,
    longitude: 69.3451,
    zoom: 5,
  },
  activeLayers: ['incidents', 'poverty', 'routes'],
  selectedDistrict: null,
  yearRange: [2010, 2024],

  setViewport: (partial) =>
    set((state) => ({
      viewport: { ...state.viewport, ...partial },
    })),

  toggleLayer: (layer) =>
    set((state) => {
      const exists = state.activeLayers.includes(layer);
      return {
        activeLayers: exists
          ? state.activeLayers.filter((l) => l !== layer)
          : [...state.activeLayers, layer],
      };
    }),

  setSelectedDistrict: (pcode) =>
    set({ selectedDistrict: pcode }),

  setYearRange: (range) =>
    set({ yearRange: range }),
}));
