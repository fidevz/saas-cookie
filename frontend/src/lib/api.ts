import { ApiError } from "@/types";
import { joinApiUrl } from "@/lib/join-url";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").trim() || "/api/v1";

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
    const response = await fetch(joinApiUrl(API_BASE, "/auth/token/refresh/"), {
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

function extractErrorMessage(data: unknown): string {
  if (typeof data === "string") return data;
  if (Array.isArray(data)) {
    return data.map((item) => extractErrorMessage(item)).join(". ");
  }
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    // Unwrap envelope: {"error": "...", "detail": <string|object>}
    if (obj.detail !== undefined) return extractErrorMessage(obj.detail);
    const messages: string[] = [];
    for (const key in obj) {
      const val = obj[key];
      const msg = extractErrorMessage(val);
      // Skip noisy field prefixes for non-field errors
      if (key === "non_field_errors" || key === "detail") {
        messages.push(msg);
      } else {
        messages.push(`${key}: ${msg}`);
      }
    }
    return messages.join(". ");
  }
  return "An unexpected error occurred";
}

class ApiClient {
  private async request<T>(
    path: string,
    options: RequestInit & { skipAuth?: boolean; skipRefresh?: boolean } = {}
  ): Promise<T> {
    const { skipAuth = false, skipRefresh = false, ...fetchOptions } = options;

    const isFormData = fetchOptions.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
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

    const response = await fetch(joinApiUrl(API_BASE, path), {
      ...fetchOptions,
      headers,
      credentials: "include",
      signal: fetchOptions.signal,
    });

    // Handle 402 — subscription required.
    // The paywall is handled at the layout level, so just throw and let callers handle it.
    if (response.status === 402) {
      throw new Error("An active subscription is required.");
    }

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
      let errorData: unknown = {};
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

  async postMultipart<T>(path: string, data: FormData): Promise<T> {
    return this.request<T>(path, { method: "POST", body: data });
  }

  async patchMultipart<T>(path: string, data: FormData): Promise<T> {
    return this.request<T>(path, { method: "PATCH", body: data });
  }

  async getBlob(path: string): Promise<{ blob: Blob; filename: string }> {
    const doFetch = (token: string | null) => {
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      return fetch(joinApiUrl(API_BASE, path), {
        method: "GET",
        headers,
        credentials: "include",
      });
    };

    let response = await doFetch(getAccessToken());

    if (response.status === 401) {
      const newToken = await handleRefresh();
      if (newToken) {
        response = await doFetch(newToken);
      } else {
        if (typeof window !== "undefined") window.location.href = "/auth/login";
        throw new Error("Session expired");
      }
    }

    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") ?? "";
    const match = disposition.match(/filename="?([^";\n]+)"?/);
    const filename = match?.[1] ?? "download";
    return { blob, filename };
  }
}

export const api = new ApiClient();
