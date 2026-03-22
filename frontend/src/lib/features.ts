import { api } from "./api";
import { FeatureFlags } from "@/types";

export async function fetchFeatureFlags(): Promise<FeatureFlags> {
  try {
    return await api.get<FeatureFlags>("/features/");
  } catch {
    // Return safe defaults if feature flags can't be fetched
    return {
      TEAMS: false,
      BILLING: true,
      NOTIFICATIONS: false,
    };
  }
}

export function useFeature(flag: keyof FeatureFlags): boolean {
  // This hook reads from the Zustand store
  // Importing here to avoid circular dependencies
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { useFeatureStore } = require("@/stores/feature-store");
  return useFeatureStore.getState().flags[flag] ?? false;
}
