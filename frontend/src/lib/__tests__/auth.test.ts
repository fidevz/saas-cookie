import { describe, it, expect, vi, beforeEach } from "vitest";
import { login, register, logout, requestPasswordReset, confirmPasswordReset } from "../auth";

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

describe("login", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls api.post with email and password, skipAuth=true", async () => {
    const { api } = await import("../api");
    const mockResponse = { access: "tok", user: { id: 1, email: "a@b.com" } };
    vi.mocked(api.post).mockResolvedValueOnce(mockResponse);

    await login("a@b.com", "pass");

    expect(api.post).toHaveBeenCalledWith(
      "/auth/login/",
      { email: "a@b.com", password: "pass" },
      { skipAuth: true }
    );
  });

  it("returns the response from the API", async () => {
    const { api } = await import("../api");
    const mockResponse = { access: "token-123", user: { id: 1, email: "test@test.com" } };
    vi.mocked(api.post).mockResolvedValueOnce(mockResponse);

    const result = await login("test@test.com", "password");
    expect(result).toEqual(mockResponse);
  });

  it("propagates errors from the API", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Invalid credentials"));

    await expect(login("bad@test.com", "wrong")).rejects.toThrow("Invalid credentials");
  });
});

describe("register", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls api.post with registration data, skipAuth=true", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockResolvedValueOnce({ access: "tok", user: {} });

    const data = { company_name: "Test Co", slug: "test-co", email: "new@test.com", password: "pass123", first_name: "New", last_name: "User" };
    await register(data);

    expect(api.post).toHaveBeenCalledWith("/auth/register/", data, { skipAuth: true });
  });
});

describe("logout", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls api.post on logout endpoint", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockResolvedValueOnce(undefined);

    await logout();
    expect(api.post).toHaveBeenCalledWith("/auth/logout/");
  });

  it("does not throw when API call fails", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Network error"));

    await expect(logout()).resolves.toBeUndefined();
  });
});

describe("requestPasswordReset", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls the correct endpoint with email", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockResolvedValueOnce(undefined);

    await requestPasswordReset("user@test.com");
    expect(api.post).toHaveBeenCalledWith(
      "/auth/password-reset/",
      { email: "user@test.com" },
      { skipAuth: true }
    );
  });
});

describe("confirmPasswordReset", () => {
  beforeEach(() => vi.clearAllMocks());

  it("calls the correct endpoint with token and password", async () => {
    const { api } = await import("../api");
    vi.mocked(api.post).mockResolvedValueOnce(undefined);

    await confirmPasswordReset("uid-token", "newpass");
    expect(api.post).toHaveBeenCalledWith(
      "/auth/password-reset/confirm/",
      { token: "uid-token", password: "newpass" },
      { skipAuth: true }
    );
  });
});
