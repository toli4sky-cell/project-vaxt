import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  apiFetch,
  clearTokens,
  getAccessToken,
  getApiBase,
  setTokens,
  type TokenPair,
} from "@/shared/api/client";

export type AuthUser = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: { code: string; name: string }[];
};

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

	const refreshUser = useCallback(async () => {
	  setLoading(true);

	  try {
		const token = getAccessToken();
		if (!token) {
		  setUser(null);
		  return;
		}

		const res = await apiFetch("/api/v1/auth/me");
		if (!res.ok) {
		  setUser(null);
		  return;
		}

		const data = (await res.json()) as AuthUser;
		setUser(data);
	  } catch (error) {
		console.error("refreshUser failed:", error);
		setUser(null);
	  } finally {
		setLoading(false);
	  }
	}, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const base = getApiBase();
    const loginPath = base ? `${base}/api/v1/auth/login` : "/api/v1/auth/login";
    const res = await fetch(loginPath, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
	if (!res.ok) {
	  const err = await res.json().catch(() => ({} as any));
	  const detail = (err as any)?.detail;

	  let message = "Ошибка входа";

	  if (typeof detail === "string") {
		message = detail;
	  } else if (Array.isArray(detail)) {
		message = detail
		  .map((item: any) => item?.msg || JSON.stringify(item))
		  .filter(Boolean)
		  .join(", ");
	  } else if (detail && typeof detail === "object") {
		message = JSON.stringify(detail);
	  }

	  throw new Error(message);
	}
    const tokens = (await res.json()) as TokenPair;
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, login, logout, refreshUser }),
    [user, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
