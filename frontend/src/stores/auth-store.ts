"use client";

import { create } from "zustand";
import { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User) => void;
  setAccessToken: (token: string) => void;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user: User) => set({ user }),

  setAccessToken: (token: string) =>
    set({ accessToken: token, isAuthenticated: true }),

  setAuth: (user: User, token: string) =>
    set({ user, accessToken: token, isAuthenticated: true, isLoading: false }),

  logout: () =>
    set({ user: null, accessToken: null, isAuthenticated: false, isLoading: false }),

  initialize: async () => {
    if (get().accessToken) {
      set({ isLoading: false });
      return;
    }
    try {
      // Attempt a silent token refresh using httpOnly cookie
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/token/refresh/`,
        { method: "POST", credentials: "include" }
      );
      if (response.ok) {
        const data = await response.json();
        const { getProfile } = await import("@/lib/auth");
        // Temporarily set token to fetch profile
        set({ accessToken: data.access, isAuthenticated: true });
        const user = await getProfile();
        set({ user, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));
