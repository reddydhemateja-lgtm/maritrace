// frontend/src/services/api.ts

// In development, connect to local backend.
// In production (Netlify), connect to Render backend.
const IS_DEV = import.meta.env.DEV;

const API_BASE = IS_DEV
  ? 'http://localhost:8000/api'
  : 'https://maritrace.onrender.com/api';

const WS_BASE = IS_DEV
  ? 'ws://localhost:8000/ws'
  : 'wss://maritrace.onrender.com/ws';
// Helper to handle fetch responses
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Try to get error message from response body
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.message) errorMessage = errorData.message;
      else if (errorData.detail) errorMessage = errorData.detail;
    } catch (_) {
      // Ignore JSON parsing errors
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export const api = {
  // Health check — increased timeout for Render cold start
  async health() {
    try {
      const res = await fetch(`${API_BASE}/health`, {
        signal: AbortSignal.timeout(60000),  // 60 seconds — enough for Render free tier cold start
      });
      return handleResponse<{ status: string; mode: string }>(res);
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Backend not responding. If this is a fresh request, wait up to 60 seconds and try again.');
    }
  },

  // Incidents
  async getIncidents() {
    const res = await fetch(`${API_BASE}/incidents/`);
    return handleResponse<any[]>(res);
  },

  async getIncident(id: string) {
    const res = await fetch(`${API_BASE}/incidents/${id}`);
    return handleResponse<any>(res);
  },

  // Vessels
  async getVessels(incidentId?: string) {
    const url = incidentId ? `${API_BASE}/vessels?incident_id=${incidentId}` : `${API_BASE}/vessels`;
    const res = await fetch(url);
    return handleResponse<any[]>(res);
  },

  // Drift
  async getDriftConditions(lat: number, lon: number) {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    const res = await fetch(`${API_BASE}/drift/conditions?${params}`);
    return handleResponse<any>(res);
  },

  // Investigation
  async getInvestigation(incidentId: string) {
    const res = await fetch(`${API_BASE}/investigation/${incidentId}`);
    return handleResponse<any>(res);
  },

  // Reports
  async generateReport(incidentId: string, format: 'pdf' | 'json' = 'pdf') {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ incident_id: incidentId, format }),
    });
    if (format === 'pdf') {
      if (!res.ok) throw new Error('Failed to generate PDF');
      return res.blob();
    }
    return handleResponse<any>(res);
  },

  // Satellite analysis
  async analyzeSatelliteImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/satellite/analyze`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<any>(res);
  },

  // AIS – get nearby vessels
  async getNearbyVessels(lat: number, lon: number, radius: number = 50) {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon), radius: String(radius) });
    const res = await fetch(`${API_BASE}/ais/nearby?${params}`);
    return handleResponse<any>(res);
  },

  // Vessel ranking (for investigation)
  async rankVessels(vessels: any[]) {
    const res = await fetch(`${API_BASE}/vessels/rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vessels }),
    });
    return handleResponse<any[]>(res);
  },
};

export const WS_URL = WS_BASE;