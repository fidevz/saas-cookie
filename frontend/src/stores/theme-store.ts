"use client";

import { create } from "zustand";

type Theme = "system" | "light" | "dark";
type ResolvedTheme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  seedFromUser: (theme: Theme) => void;
  resolveTheme: () => void;
}

function getResolvedTheme(theme: Theme): ResolvedTheme {
  if (theme !== "system") return theme;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: "light",
  resolvedTheme: "light",

  setTheme: (theme: Theme) => {
    const resolvedTheme = getResolvedTheme(theme);
    set({ theme, resolvedTheme });
    // Persist to backend (fire-and-forget)
    import("@/lib/api").then(({ api }) => {
      api.patch("/users/me/", { theme }).catch(() => {});
    });
  },

  seedFromUser: (theme: Theme) => {
    set({ theme, resolvedTheme: getResolvedTheme(theme) });
  },

  resolveTheme: () => {
    set({ resolvedTheme: getResolvedTheme(get().theme) });
  },
}));
