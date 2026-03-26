import { api } from "./api";
import { User, RegisterData } from "@/types";

export interface LoginResponse {
  access: string;
  tenant_slug: string | null;
  user: User;
}

export interface RegisterResponse {
  access: string;
  tenant_slug: string;
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
  await api.post<void>("/auth/password-reset/", { email }, { skipAuth: true });
}

export async function confirmPasswordReset(token: string, password: string): Promise<void> {
  await api.post<void>("/auth/password-reset/confirm/", { token, password }, { skipAuth: true });
}

export async function getProfile(): Promise<User> {
  return api.get<User>("/users/me/");
}

export async function resendVerificationEmail(email: string): Promise<void> {
  await api.post<void>("/auth/resend-verification/", { email }, { skipAuth: true });
}

export interface VerifyEmailResponse {
  detail: string;
  code: string;
  tenant_slug: string | null;
}

export async function verifyEmail(key: string): Promise<VerifyEmailResponse> {
  return api.post<VerifyEmailResponse>("/auth/verify-email/", { key }, { skipAuth: true });
}

export interface ExchangeCodeResponse {
  access: string;
  user: User;
}

export async function exchangeCode(code: string): Promise<ExchangeCodeResponse> {
  return api.post<ExchangeCodeResponse>("/auth/exchange-code/", { code }, { skipAuth: true });
}

export async function checkSlug(slug: string): Promise<{ available: boolean; suggestion?: string; error?: string }> {
  return api.get<{ available: boolean; suggestion?: string; error?: string }>(
    `/auth/check-slug/?slug=${encodeURIComponent(slug)}`
  );
}
