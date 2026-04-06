const ACCESS = "access_token";
const REFRESH = "refresh_token";

export function getApiBase(): string {
  const v = import.meta.env.VITE_API_URL;
  return v && v.length > 0 ? v.replace(/\/$/, "") : "";
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS, access);
  localStorage.setItem(REFRESH, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
}

export type TokenPair = { access_token: string; refresh_token: string; token_type: string };

async function refreshSession(): Promise<string | null> {
  const rt = getRefreshToken();
  if (!rt) return null;
  const base = getApiBase();
  const res = await fetch(`${base}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: rt }),
  });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  const data = (await res.json()) as TokenPair;
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const base = getApiBase();
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let res = await fetch(url, { ...init, headers });
  if (res.status === 401 && path !== "/api/v1/auth/refresh" && path !== "/api/v1/auth/login") {
    const newAccess = await refreshSession();
    if (newAccess) {
      headers.set("Authorization", `Bearer ${newAccess}`);
      res = await fetch(url, { ...init, headers });
    }
  }
  return res;
}
