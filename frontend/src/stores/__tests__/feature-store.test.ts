import { describe, it, expect, beforeEach } from "vitest";
import { useFeatureStore } from "../feature-store";

describe("useFeatureStore", () => {
  beforeEach(() => {
    useFeatureStore.setState({
      flags: { TEAMS: false, BILLING: true, NOTIFICATIONS: false, REQUIRE_SUBSCRIPTION: false },
      isLoaded: false,
    });
  });

  it("has correct default flags", () => {
    const { flags, isLoaded } = useFeatureStore.getState();
    expect(flags.TEAMS).toBe(false);
    expect(flags.BILLING).toBe(true);
    expect(flags.NOTIFICATIONS).toBe(false);
    expect(isLoaded).toBe(false);
  });

  it("setFlags updates all flags and sets isLoaded=true", () => {
    useFeatureStore.getState().setFlags({ TEAMS: true, BILLING: true, NOTIFICATIONS: true, REQUIRE_SUBSCRIPTION: false });
    const { flags, isLoaded } = useFeatureStore.getState();
    expect(flags.TEAMS).toBe(true);
    expect(flags.BILLING).toBe(true);
    expect(flags.NOTIFICATIONS).toBe(true);
    expect(isLoaded).toBe(true);
  });

  it("setFlags can disable flags", () => {
    useFeatureStore.getState().setFlags({ TEAMS: false, BILLING: false, NOTIFICATIONS: false, REQUIRE_SUBSCRIPTION: false });
    const { flags } = useFeatureStore.getState();
    expect(flags.TEAMS).toBe(false);
    expect(flags.BILLING).toBe(false);
    expect(flags.NOTIFICATIONS).toBe(false);
  });
});
