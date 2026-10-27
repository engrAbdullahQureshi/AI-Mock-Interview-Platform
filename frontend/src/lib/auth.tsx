"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, tokenStore, type ApiError } from "./api";
import type { User, TokenResponse } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean; // true during initial session rehydrate
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const applyToken = useCallback((data: TokenResponse) => {
    tokenStore.setAccess(data.access_token);
    tokenStore.setRefresh(data.refresh_token);
    setUser(data.user);
  }, []);

  // Rehydrate session on mount using the stored refresh token
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const refresh = tokenStore.getRefresh();
      if (!refresh) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.me(); // api layer auto-refreshes the access token
        if (!cancelled) setUser(me);
      } catch {
        tokenStore.clear();
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      applyToken(await api.login(email, password));
    },
    [applyToken],
  );

  const register = useCallback(
    async (username: string, email: string, password: string) => {
      applyToken(await api.register(username, email, password));
    },
    [applyToken],
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

/** Guard a page: redirects to /login once rehydrate finishes with no user.
 *  Returns { ready } — true when it's safe to render protected content. */
export function useRequireAuth(): { ready: boolean; user: User | null } {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);
  return { ready: !loading && !!user, user };
}

export function isApiError(e: unknown): e is ApiError {
  return typeof e === "object" && e !== null && "status" in e;
}
