import { create } from 'zustand';

interface ScraperStore {
  selectedScraper: string | null;
  statusFilter: 'all' | 'healthy' | 'warning' | 'error' | 'inactive';
  searchQuery: string;
  setSelectedScraper: (name: string | null) => void;
  setStatusFilter: (filter: 'all' | 'healthy' | 'warning' | 'error' | 'inactive') => void;
  setSearchQuery: (query: string) => void;
}

export const useScraperStore = create<ScraperStore>((set) => ({
  selectedScraper: null,
  statusFilter: 'all',
  searchQuery: '',
  setSelectedScraper: (name) => set({ selectedScraper: name }),
  setStatusFilter: (filter) => set({ statusFilter: filter }),
  setSearchQuery: (query) => set({ searchQuery: query }),
}));
