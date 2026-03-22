import { ApiError } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

function getAccessToken(): string | null {
  // Access token is stored in Zustand memory store
  // We import lazily to avoid circular deps and SSR issues
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useAuthStore } = require("@/stores/auth-store");
    return useAuthStore.getState().accessToken;
  } catch {
    return null;
  }
}

async function handleRefresh(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) return null;
    const data = await response.json();
    const { useAuthStore } = await import("@/stores/auth-store");
    useAuthStore.getState().setAccessToken(data.access);
    return data.access as string;
  } catch {
    return null;
  }
}

function extractErrorMessage(data: ApiError): string {
  if (data.detail) return data.detail;
  const messages: string[] = [];
  for (const key in data) {
    const val = data[key];
    if (Array.isArray(val)) {
      messages.push(`${key}: ${val.join(", ")}`);
    } else if (typeof val === "string") {
      messages.push(val);
    }
  }
  return messages.join(". ") || "An unexpected error occurred";
}

class ApiClient {
  private async request<T>(
    path: string,
    options: RequestInit & { skipAuth?: boolean; skipRefresh?: boolean } = {}
  ): Promise<T> {
    const { skipAuth = false, skipRefresh = false, ...fetchOptions } = options;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(fetchOptions.headers as Record<string, string>),
    };

    if (!skipAuth) {
      const token = getAccessToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const csrfToken = getCookie("csrftoken");
    if (csrfToken && ["POST", "PUT", "PATCH", "DELETE"].includes(fetchOptions.method ?? "")) {
      headers["X-CSRFToken"] = csrfToken;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      headers,
      credentials: "include",
    });

    // Handle 401 with token refresh
    if (response.status === 401 && !skipRefresh && !skipAuth) {
      const newToken = await handleRefresh();
      if (newToken) {
        return this.request<T>(path, { ...options, skipRefresh: true });
      }
      // Refresh failed — redirect to login
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      throw new Error("Session expired");
    }

    if (!response.ok) {
      let errorData: ApiError = {};
      try {
        errorData = await response.json();
      } catch {
        // Ignore JSON parse errors
      }
      throw new Error(extractErrorMessage(errorData));
    }

    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return response.json() as Promise<T>;
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "GET" });
  }

  async post<T>(path: string, data?: unknown, options?: { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
  }

  async patch<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async put<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async delete(path: string): Promise<void> {
    return this.request<void>(path, { method: "DELETE" });
  }
}

export const api = new ApiClient();
