import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock auth store before importing api
vi.mock("@/stores/auth-store", () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ accessToken: null })),
  },
}));

import { api } from "../api";
import { useAuthStore } from "@/stores/auth-store";

function mockFetch(status: number, body?: unknown) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body ?? {}),
  } as Response);
}

describe("ApiClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthStore.getState).mockReturnValue({ accessToken: null } as ReturnType<typeof useAuthStore.getState>);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("GET", () => {
    it("makes a GET request to the correct URL", async () => {
      mockFetch(200, { data: "test" });
      await api.get("/test/");
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/"),
        expect.objectContaining({ method: "GET" })
      );
    });

    it("does not include Authorization header when token is null", async () => {
      mockFetch(200, {});
      await api.get("/public/");
      const [, options] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
      // When there is no access token, Authorization should not be set
      const headers = options.headers as Record<string, string>;
      expect(headers["Authorization"]).toBeUndefined();
    });


    it("includes credentials: include on every request", async () => {
      mockFetch(200, {});
      await api.get("/any/");
      const [, options] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
      expect(options.credentials).toBe("include");
    });
  });

  describe("POST", () => {
    it("serializes body to JSON", async () => {
      mockFetch(200, { ok: true });
      await api.post("/create/", { name: "test", value: 42 });
      const [, options] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
      expect(options.body).toBe(JSON.stringify({ name: "test", value: 42 }));
    });

    it("sends Content-Type: application/json", async () => {
      mockFetch(200, {});
      await api.post("/create/", {});
      const [, options] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
      expect((options.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
    });
  });

  describe("Error handling", () => {
    it("throws error with detail message on non-ok response", async () => {
      mockFetch(400, { detail: "Bad request error" });
      await expect(api.get("/bad/")).rejects.toThrow("Bad request error");
    });

    it("throws error with field errors on validation error", async () => {
      mockFetch(400, { email: ["This field is required."] });
      await expect(api.get("/bad/")).rejects.toThrow("email: This field is required.");
    });

    it("throws generic error when response body cannot be parsed", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("No body")),
      } as unknown as Response);
      await expect(api.get("/server-error/")).rejects.toThrow("An unexpected error occurred");
    });
  });

  describe("204 No Content", () => {
    it("returns undefined for 204 responses", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      } as unknown as Response);
      const result = await api.delete("/resource/1/");
      expect(result).toBeUndefined();
    });
  });
});
