import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchFeatureFlags } from "../features";

// Mock the api module
vi.mock("../api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("fetchFeatureFlags", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns API response on success", async () => {
    const { api } = await import("../api");
    vi.mocked(api.get).mockResolvedValueOnce({
      TEAMS: true,
      BILLING: true,
      NOTIFICATIONS: true,
    });

    const flags = await fetchFeatureFlags();
    expect(flags).toEqual({ TEAMS: true, BILLING: true, NOTIFICATIONS: true });
    expect(api.get).toHaveBeenCalledWith("/features/");
  });

  it("returns safe defaults when API call fails", async () => {
    const { api } = await import("../api");
    vi.mocked(api.get).mockRejectedValueOnce(new Error("Network error"));

    const flags = await fetchFeatureFlags();
    expect(flags).toEqual({ TEAMS: false, BILLING: true, NOTIFICATIONS: false });
  });

  it("always returns BILLING=true as default on failure", async () => {
    const { api } = await import("../api");
    vi.mocked(api.get).mockRejectedValueOnce(new Error("Timeout"));

    const { BILLING } = await fetchFeatureFlags();
    expect(BILLING).toBe(true);
  });
});
