import type {
  Alert,
  DashboardSummary,
  Facility,
  HistoricalPoint,
  ThermalEvent,
} from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");

export type MapEventFeature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: string;
    eventId: string;
    classification: string;
    riskLevel: string;
    riskScore: number;
    state: string | null;
    district: string | null;
  };
};

export type MapFacilityFeature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: string;
    facilityId: string;
    name: string;
    facilityType: string;
    state: string;
    district: string;
  };
};

export type GeoJsonResponse<T> = { type: "FeatureCollection"; features: T[] };
export type PaginatedEvents = { items: ThermalEvent[]; total: number; page: number; pageSize: number };
export type ReportResponse = {
  reportType: string;
  generatedAt: string;
  disclaimer: string;
  event: ThermalEvent;
};

export type EventQuery = {
  page?: number;
  pageSize?: number;
  riskLevel?: string;
  classification?: string;
  state?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
};

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP status when the server did not return JSON.
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

function queryString(query: EventQuery) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value && value !== "ALL") params.set(key, String(value));
  });
  const value = params.toString();
  return value ? `?${value}` : "";
}

export const api = {
  baseUrl: API_BASE_URL,
  getHealth: () => request<{ status: string; demo_mode: boolean; checks: Record<string, { status: string; detail: string }> }>("/health"),
  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
  getEvents: (query: EventQuery = {}) => request<PaginatedEvents>(`/events${queryString(query)}`),
  getAllEvents: async (query: Omit<EventQuery, "page" | "pageSize"> = {}) => {
    const firstPage = await api.getEvents({ ...query, page: 1, pageSize: 200 });
    if (firstPage.total <= firstPage.items.length) return firstPage.items;
    const pages = await Promise.all(
      Array.from({ length: Math.ceil(firstPage.total / 200) - 1 }, (_, index) =>
        api.getEvents({ ...query, page: index + 2, pageSize: 200 }),
      ),
    );
    return [firstPage, ...pages].flatMap((page) => page.items);
  },
  getEvent: (eventId: string) => request<ThermalEvent>(`/events/${encodeURIComponent(eventId)}`),
  getEventHistory: (eventId: string) => request<HistoricalPoint[]>(`/events/${encodeURIComponent(eventId)}/history`),
  analyzeEvent: (eventId: string) => request<ThermalEvent>(`/events/${encodeURIComponent(eventId)}/analyze`, { method: "POST" }),
  submitFeedback: (eventId: string, decision: string, analystNote?: string) =>
    request<{ id: number; eventId: string; decision: string; createdAt: string }>(`/events/${encodeURIComponent(eventId)}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, analystNote }),
    }),
  getPriority: (riskLevel?: string) => request<PaginatedEvents>(`/priority${queryString({ riskLevel, page: 1, pageSize: 200 })}`),
  getAlerts: (status?: string) => request<Alert[]>(`/alerts${queryString({ status })}`),
  resolveAlert: (alertId: string) => request<Alert>(`/alerts/${encodeURIComponent(alertId)}/resolve`, { method: "POST" }),
  getFacilities: () => request<Facility[]>("/facilities"),
  getMapEvents: () => request<GeoJsonResponse<MapEventFeature>>("/map/events"),
  getMapFacilities: () => request<GeoJsonResponse<MapFacilityFeature>>("/map/facilities"),
  generateReport: (eventId: string) => request<ReportResponse>(`/reports/events/${encodeURIComponent(eventId)}`, { method: "POST" }),
};

export { ApiError };
