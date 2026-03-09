// In production (single Railway service) leave VITE_API_BASE_URL unset → relative URL.
// For local dev set VITE_API_BASE_URL=http://localhost:8000 in frontend/.env.local
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> ?? {}),
  };

  // Don't set Content-Type for FormData — browser sets it with boundary
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
