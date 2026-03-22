import { api } from "./api";
import { User, RegisterData } from "@/types";

export interface LoginResponse {
  access: string;
  user: User;
}

export interface RegisterResponse {
  access: string;
  user: User;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return api.post<LoginResponse>("/auth/login/", { email, password }, { skipAuth: true });
}

export async function register(data: RegisterData): Promise<RegisterResponse> {
  return api.post<RegisterResponse>("/auth/register/", data, { skipAuth: true });
}

export async function logout(): Promise<void> {
  try {
    await api.post<void>("/auth/logout/");
  } catch {
    // Best-effort logout — clear local state regardless
  }
}

export async function refreshToken(): Promise<string> {
  const response = await api.post<{ access: string }>(
    "/auth/token/refresh/",
    undefined,
    { skipAuth: true }
  );
  return response.access;
}

export async function getGoogleAuthUrl(): Promise<string> {
  const response = await api.get<{ url: string }>("/auth/google/");
  return response.url;
}

export async function requestPasswordReset(email: string): Promise<void> {
  await api.post<void>("/auth/password/reset/", { email }, { skipAuth: true });
}

export async function confirmPasswordReset(token: string, password: string): Promise<void> {
  await api.post<void>("/auth/password/reset/confirm/", { token, password }, { skipAuth: true });
}

export async function getProfile(): Promise<User> {
  return api.get<User>("/auth/me/");
}
