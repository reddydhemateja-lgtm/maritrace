const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  recentSpills: (region?: string) =>
    request(`/recent-spills${region ? `?region=${region}` : ""}`),
  getSpill: (id: number) => request(`/spills/${id}`),
  regions: () => request("/regions"),
  aisVessels: (bbox?: string) =>
    request(`/ais/vessels${bbox ? `?bbox=${bbox}` : ""}`),
  hindcast: (slick_id: number, hours_back = 72) =>
    request("/drift/hindcast", {
      method: "POST",
      body: JSON.stringify({ slick_id, hours_back }),
    }),
  investigate: (slick_id: number) =>
    request("/investigate", {
      method: "POST",
      body: JSON.stringify({ slick_id }),
    }),
  listInvestigations: () => request("/investigate"),
  getInvestigation: (caseNumber: string) =>
    request(`/investigate/${caseNumber}`),
  satelliteSearch: (bbox: string) => request(`/satellite/search?bbox=${bbox}`),
  reportUrl: (caseNumber: string) =>
    `${BASE}/investigate/${caseNumber}/report.pdf`,
};