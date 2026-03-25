"use client";

import { create } from "zustand";
import { FeatureFlags } from "@/types";

interface FeatureState {
  flags: FeatureFlags;
  isLoaded: boolean;
  setFlags: (flags: FeatureFlags) => void;
}

export const useFeatureStore = create<FeatureState>((set) => ({
  flags: {
    TEAMS: true,
    BILLING: true,
    NOTIFICATIONS: true,
    REQUIRE_SUBSCRIPTION: false,
  },
  isLoaded: false,

  setFlags: (flags: FeatureFlags) => set({ flags, isLoaded: true }),
}));
