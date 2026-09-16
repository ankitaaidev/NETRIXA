const API_BASE_URL = "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => request("/api/dashboard/summary"),

  getMapEvents: () => request("/api/map/events"),

  getMapFacilities: () => request("/api/map/facilities"),

  // Events
  getAllEvents: () => request("/api/events?page=1&pageSize=2000"),
  getHistoricalRiskTrend: () => request("/api/events/historical-risk-trend"),

  getEvent: (eventId: string) => request(`/api/events/${eventId}`),

  // Facilities
  getFacilities: () => request("/api/facilities"),

  // Priority Center
  getPriority: () => request("/api/priority"),

  // Alerts
  getAlerts: () => request("/api/alerts"),

  resolveAlert: (id: string) =>
    request(`/api/alerts/${id}/resolve`, {
      method: "POST",
    }),

  // Analyst feedback
  submitFeedback: (eventId: string, decision: string) =>
    request(`/api/events/${eventId}/feedback`, {
      method: "POST",
      body: JSON.stringify({
        decision,
      }),
    }),

  // Reports
  generateReport: (eventId: string) =>
    request(`/api/reports/events/${eventId}`, {
      method: "POST",
    }),
  downloadReportPdf: async (eventId: string) => {
    const response = await fetch(
      `${API_BASE_URL}/api/reports/events/${eventId}/pdf`,
    );

    if (!response.ok) {
      throw new Error(
        `PDF download failed: ${response.status} ${response.statusText}`,
      );
    }

    return response.blob();
  },

  // Health
  getHealth: () => request("/health"),
};
