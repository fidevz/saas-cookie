/**
 * API helpers for creating test data directly via backend API.
 * Use in test setup to provision users, tenants, etc. without going through the UI.
 */

const API_URL = process.env.API_URL || "http://localhost:8000/api/v1";

export interface TestUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  access_token: string;
}

export interface TestTenant {
  id: number;
  name: string;
  slug: string;
}

/**
 * Register a new user and return their data + access token.
 */
export async function createTestUser(data: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}): Promise<TestUser & { access_token: string }> {
  const response = await fetch(`${API_URL}/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: data.email,
      password: data.password,
      first_name: data.first_name || "Test",
      last_name: data.last_name || "User",
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to create test user: ${JSON.stringify(error)}`);
  }

  return response.json();
}

/**
 * Login an existing user and return their access token.
 */
export async function loginTestUser(
  email: string,
  password: string
): Promise<string> {
  const response = await fetch(`${API_URL}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(`Login failed for ${email}`);
  }

  const data = await response.json();
  return data.access;
}

/**
 * Get the current user's profile.
 */
export async function getProfile(
  accessToken: string
): Promise<TestUser> {
  const response = await fetch(`${API_URL}/users/me/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch profile");
  }

  return response.json();
}

/**
 * Invite a member to the current tenant.
 */
export async function inviteMember(
  accessToken: string,
  email: string,
  role: "admin" | "member" = "member"
): Promise<{ token: string }> {
  const response = await fetch(`${API_URL}/teams/invitations/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ email, role }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to invite member: ${JSON.stringify(error)}`);
  }

  return response.json();
}

/**
 * Accept an invitation by token.
 */
export async function acceptInvitation(
  token: string,
  accessToken?: string
): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_URL}/teams/accept-invite/${token}/`, {
    method: "POST",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to accept invitation");
  }
}

/**
 * Get notifications for the current user.
 */
export async function getNotifications(accessToken: string) {
  const response = await fetch(`${API_URL}/notifications/notifications/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch notifications");
  }

  return response.json();
}

/**
 * Generate a unique test email to avoid conflicts.
 */
export function uniqueEmail(prefix = "test"): string {
  return `${prefix}+${Date.now()}@example.com`;
}
