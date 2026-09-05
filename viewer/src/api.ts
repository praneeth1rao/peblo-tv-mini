/**
 * Viewer API client.
 * IMPORTANT: This client ONLY uses /catalog endpoints.
 * It NEVER calls /admin, /shows, /episodes, or any other authenticated endpoint.
 */

const CATALOG_BASE = "/catalog";

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`${CATALOG_BASE}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  getCatalogue: () => request<any>(""),

  searchCatalogue: (params: Record<string, string>) => {
    const q = new URLSearchParams(params).toString();
    return request<any>(`/search${q ? `?${q}` : ""}`);
  },
};
