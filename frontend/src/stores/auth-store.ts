"use client";

import { create } from "zustand";
import { User } from "@/types";

// Deduplicate concurrent initialize() calls (e.g. React Strict Mode double-invoke).
// Without this, two concurrent calls both try to refresh; the first rotates the
// token (blacklisting the old one), and the second gets 401 → logout().
let _initPromise: Promise<void> | null = null;

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  tenantSlug: string | null;
  setUser: (user: User) => void;
  setAccessToken: (token: string) => void;
  setAuth: (user: User, token: string, tenantSlug?: string | null) => void;
  logout: () => void;
  initialize: () => Promise<void>;
}

function cookieDomain(): string {
  if (typeof window === "undefined") return "";
  const base = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  // Browsers don't share cookies across subdomains of localhost — omit the
  // domain attribute so the cookie is set for the current host only.
  if (base === "localhost") return "";
  return `domain=.${base}; `;
}

function setTenantCookie(slug: string | null | undefined) {
  if (typeof document === "undefined") return;
  const d = cookieDomain();
  if (slug) {
    document.cookie = `tenant_slug=${slug}; path=/; ${d}SameSite=Lax; max-age=604800`;
  } else {
    document.cookie = `tenant_slug=; path=/; ${d}expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,
  tenantSlug: null,

  setUser: (user: User) => set({ user }),

  setAccessToken: (token: string) => {
    if (typeof document !== "undefined") {
      document.cookie = `auth_session=1; path=/; ${cookieDomain()}SameSite=Lax`;
    }
    set({ accessToken: token, isAuthenticated: true });
  },

  setAuth: (user: User, token: string, tenantSlug?: string | null) => {
    if (typeof document !== "undefined") {
      document.cookie = `auth_session=1; path=/; ${cookieDomain()}SameSite=Lax`;
    }
    setTenantCookie(tenantSlug);
    set({
      user,
      accessToken: token,
      isAuthenticated: true,
      isLoading: false,
      tenantSlug: tenantSlug ?? null,
    });
  },

  logout: () => {
    if (typeof document !== "undefined") {
      document.cookie = `auth_session=; path=/; ${cookieDomain()}expires=Thu, 01 Jan 1970 00:00:00 GMT`;
      // Also clear without domain to cover cookies set on other subdomains (e.g. localhost vs lume.localhost)
      document.cookie = `auth_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
      document.cookie = `tenant_slug=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
    }
    setTenantCookie(null);
    set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false, tenantSlug: null });
  },

  initialize: async () => {
    if (get().accessToken) {
      set({ isLoading: false });
      return;
    }
    // Skip the refresh attempt when there's no session cookie — avoids a
    // guaranteed 400 for anonymous users who have no refresh_token to send.
    // auth_session=1 is always set by setAuth() after a successful login,
    // including on tenant subdomains via the code-exchange callback.
    if (typeof document !== "undefined" && !document.cookie.includes("auth_session=1")) {
      set({ isLoading: false });
      return;
    }
    // If an initialize() is already in flight, wait for it instead of starting
    // a second refresh (which would receive a 401 after token rotation).
    if (_initPromise) {
      return _initPromise;
    }
    _initPromise = (async () => {
      try {
        // Attempt a silent token refresh using the httpOnly refresh_token cookie.
        // We always try — the refresh_token cookie is scoped to the API origin
        // (localhost:8000) and works across frontend subdomains, unlike auth_session.
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/token/refresh/`,
          { method: "POST", credentials: "include" }
        );
        if (response.ok) {
          const data = await response.json();
          const { getProfile } = await import("@/lib/auth");
          if (typeof document !== "undefined") {
            document.cookie = `auth_session=1; path=/; ${cookieDomain()}SameSite=Lax`;
          }
          set({ accessToken: data.access, isAuthenticated: true });
          try {
            const user = await getProfile();
            setTenantCookie(user.tenant_slug);
            const { useThemeStore } = await import("@/stores/theme-store");
            useThemeStore.getState().seedFromUser(user.theme ?? "system");
            set({ user, isLoading: false, tenantSlug: user.tenant_slug ?? null });
          } catch {
            // Profile fetch may fail with 402 (no subscription) — the user is
            // still authenticated so don't logout, just finish loading.
            set({ isLoading: false });
          }
        } else {
          // Refresh failed — clear session cookies so the middleware doesn't
          // redirect the user back to a protected route they can't access,
          // causing an infinite loop between /dashboard and /auth/login.
          get().logout();
        }
      } catch {
        get().logout();
      } finally {
        _initPromise = null;
      }
    })();
    return _initPromise;
  },
}));
