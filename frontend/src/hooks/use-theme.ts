"use client";

import { useThemeStore } from "@/stores/theme-store";

export function useTheme() {
  const { theme, resolvedTheme, setTheme } = useThemeStore();
  return { theme, resolvedTheme, setTheme };
}
