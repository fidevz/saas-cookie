import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../auth-store";
import type { User } from "@/types";

const mockUser: User = {
  id: 1,
  email: "test@example.com",
  first_name: "Test",
  last_name: "User",
  is_first_login: false, tenant_slug: null,
};

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: true,
    });
  });

  it("has correct initial state", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(true);
  });

  it("setAuth sets user, token, isAuthenticated=true, isLoading=false", () => {
    useAuthStore.getState().setAuth(mockUser, "access-token-123");
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.accessToken).toBe("access-token-123");
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it("setUser updates only user", () => {
    useAuthStore.setState({ accessToken: "tok", isAuthenticated: true });
    useAuthStore.getState().setUser(mockUser);
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.accessToken).toBe("tok");
    expect(state.isAuthenticated).toBe(true);
  });

  it("setAccessToken sets token and marks isAuthenticated=true", () => {
    useAuthStore.getState().setAccessToken("new-token");
    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("new-token");
    expect(state.isAuthenticated).toBe(true);
  });

  it("logout clears all auth state", () => {
    useAuthStore.getState().setAuth(mockUser, "tok");
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });
});
