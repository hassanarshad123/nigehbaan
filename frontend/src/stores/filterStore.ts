import { create } from 'zustand';
import type { IncidentType } from '@/types';

interface FilterState {
  selectedProvince: string | null;
  yearRange: [number, number];
  selectedTypes: IncidentType[];
  setSelectedProvince: (province: string | null) => void;
  setYearRange: (range: [number, number]) => void;
  toggleType: (type: IncidentType) => void;
  setSelectedTypes: (types: IncidentType[]) => void;
  resetFilters: () => void;
}

const DEFAULT_YEAR_RANGE: [number, number] = [2010, 2024];

export const useFilterStore = create<FilterState>((set) => ({
  selectedProvince: null,
  yearRange: DEFAULT_YEAR_RANGE,
  selectedTypes: [],

  setSelectedProvince: (province) =>
    set({ selectedProvince: province }),

  setYearRange: (range) =>
    set({ yearRange: range }),

  toggleType: (type) =>
    set((state) => {
      const exists = state.selectedTypes.includes(type);
      return {
        selectedTypes: exists
          ? state.selectedTypes.filter((t) => t !== type)
          : [...state.selectedTypes, type],
      };
    }),

  setSelectedTypes: (types) =>
    set({ selectedTypes: types }),

  resetFilters: () =>
    set({
      selectedProvince: null,
      yearRange: DEFAULT_YEAR_RANGE,
      selectedTypes: [],
    }),
}));
