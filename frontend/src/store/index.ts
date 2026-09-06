import { create } from 'zustand';
import type { ThermalEvent, RiskLevel } from '../types';
import { ALL_EVENTS } from '../data/mockData';

interface Filters {
  riskLevel: RiskLevel | 'ALL';
  classification: string;
  state: string;
  dateFrom: string;
  dateTo: string;
  search: string;
}

interface AppState {
  filters: Filters;
  selectedEventId: string | null;
  sidebarCollapsed: boolean;
  setFilter: (key: keyof Filters, value: string) => void;
  resetFilters: () => void;
  setSelectedEvent: (id: string | null) => void;
  toggleSidebar: () => void;
  filteredEvents: () => ThermalEvent[];
}

const defaultFilters: Filters = {
  riskLevel: 'ALL',
  classification: 'ALL',
  state: 'ALL',
  dateFrom: '',
  dateTo: '',
  search: '',
};

export const useAppStore = create<AppState>((set, get) => ({
  filters: defaultFilters,
  selectedEventId: null,
  sidebarCollapsed: false,

  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),

  resetFilters: () => set({ filters: defaultFilters }),

  setSelectedEvent: (id) => set({ selectedEventId: id }),

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  filteredEvents: () => {
    const { filters } = get();
    return ALL_EVENTS.filter((e) => {
      if (filters.riskLevel !== 'ALL' && e.riskLevel !== filters.riskLevel) return false;
      if (filters.classification !== 'ALL' && e.classification !== filters.classification) return false;
      if (filters.state !== 'ALL' && e.state !== filters.state) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        if (
          !e.eventId.toLowerCase().includes(q) &&
          !e.state.toLowerCase().includes(q) &&
          !e.district.toLowerCase().includes(q) &&
          !(e.facilityName?.toLowerCase().includes(q) ?? false)
        ) return false;
      }
      return true;
    });
  },
}));
