const API_BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  // Don't set Content-Type for FormData
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string; role: string; username: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  // Shows
  listShows: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/shows${q}`);
  },
  getShow: (id: string) => request<any>(`/shows/${id}`),
  createShow: (data: any) => request<any>("/shows", { method: "POST", body: JSON.stringify(data) }),
  updateShow: (id: string, data: any) => request<any>(`/shows/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteShow: (id: string) => request<void>(`/shows/${id}`, { method: "DELETE" }),

  // Seasons
  listSeasons: (showId: string) => request<any[]>(`/seasons?show_id=${showId}`),
  createSeason: (data: any) => request<any>("/seasons", { method: "POST", body: JSON.stringify(data) }),
  updateSeason: (id: string, data: any) => request<any>(`/seasons/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteSeason: (id: string) => request<void>(`/seasons/${id}`, { method: "DELETE" }),

  // Episodes
  listEpisodes: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/episodes${q}`);
  },
  getEpisode: (id: string) => request<any>(`/episodes/${id}`),
  createEpisode: (data: any) => request<any>("/episodes", { method: "POST", body: JSON.stringify(data) }),
  updateEpisode: (id: string, data: any) => request<any>(`/episodes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteEpisode: (id: string) => request<void>(`/episodes/${id}`, { method: "DELETE" }),

  // Artwork
  listArtwork: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/artwork${q}`);
  },
  uploadArtwork: (formData: FormData) =>
    request<any>("/artwork", { method: "POST", body: formData }),
  deleteArtwork: (id: string) => request<void>(`/artwork/${id}`, { method: "DELETE" }),

  // Admin
  getValidationReport: () => request<any>("/admin/validation-report"),
  publish: () => request<any>("/admin/catalog/publish", { method: "POST" }),
  listPublishRuns: () => request<any[]>("/admin/publish-runs"),
};
