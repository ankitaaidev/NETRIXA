import { create } from 'zustand';
import type { ThermalEvent, RiskLevel } from '../types';
import { ALL_EVENTS } from '../data/mockData';
import { api } from '../services/api';

const FALLBACK_EVENTS = ALL_EVENTS.map((event) => ({ ...event, id: event.eventId }));

interface Filters {
  riskLevel: RiskLevel | 'ALL';
  classification: string;
  state: string;
  dateFrom: string;
  dateTo: string;
  search: string;
}

interface AppState {
  events: ThermalEvent[];
  eventsLoading: boolean;
  eventsError: string | null;
  dataSource: 'backend' | 'demo-fallback';
  filters: Filters;
  selectedEventId: string | null;
  sidebarCollapsed: boolean;
  setFilter: (key: keyof Filters, value: string) => void;
  resetFilters: () => void;
  setSelectedEvent: (id: string | null) => void;
  toggleSidebar: () => void;
  loadEvents: () => Promise<void>;
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
  events: FALLBACK_EVENTS,
  eventsLoading: true,
  eventsError: null,
  dataSource: 'demo-fallback',
  filters: defaultFilters,
  selectedEventId: null,
  sidebarCollapsed: false,

  setFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),

  resetFilters: () => set({ filters: defaultFilters }),

  setSelectedEvent: (id) => set({ selectedEventId: id }),

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  loadEvents: async () => {
    set({ eventsLoading: true, eventsError: null });
    try {
      const events = await api.getAllEvents();
      set({ events, eventsLoading: false, dataSource: 'backend' });
    } catch (error) {
      set({
        events: FALLBACK_EVENTS,
        eventsLoading: false,
        dataSource: 'demo-fallback',
        eventsError: error instanceof Error ? error.message : 'Backend unavailable. Showing demo data.',
      });
    }
  },

  filteredEvents: () => {
    const { filters } = get();
    return get().events.filter((e) => {
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
