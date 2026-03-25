import { test as base, Page, Browser } from "@playwright/test";
import { uniqueEmail, createTestUser } from "../utils/api-helpers";

const API_URL = process.env.API_URL || "http://localhost:8000/api/v1";
const BASE_URL = process.env.BASE_URL || "http://localhost:3001";
const BASE_PORT = new URL(BASE_URL).port || "3001";

interface FreshUser {
  email: string;
  token: string;
  tenantSlug: string;
}

export interface AuthFixtures {
  /** Page authenticated as the default test user (from seed data) */
  authenticatedPage: Page;
  /** Page authenticated as a freshly created test user */
  freshUserPage: Page;
  /** The access token of the freshly created user */
  freshUserToken: string;
  /** The email of the freshly created user */
  freshUserEmail: string;
}

/**
 * Creates a browser context scoped to a tenant subdomain (e.g. test-company.localhost:3001).
 * Mocks the token refresh endpoint so the auth store initialises without needing
 * the httpOnly refresh_token cookie, which is only set on the root domain after login.
 */
async function createTenantPage(
  browser: Browser,
  accessToken: string,
  tenantSlug: string
): Promise<{ page: Page; cleanup: () => Promise<void> }> {
  const tenantBaseURL = `http://${tenantSlug}.localhost:${BASE_PORT}`;
  const context = await browser.newContext({ baseURL: tenantBaseURL });

  // Stub the token-refresh call so the auth store's initialize() succeeds
  // without needing the httpOnly refresh_token cookie on the subdomain.
  const page = await context.newPage();
  await page.route("**/auth/token/refresh/", (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access: accessToken }),
    });
  });

  // Set session cookies on the tenant subdomain so the Next.js middleware
  // allows access to protected routes before initialize() completes.
  await context.addCookies([
    {
      name: "auth_session",
      value: "1",
      domain: `${tenantSlug}.localhost`,
      path: "/",
      sameSite: "Lax",
    },
    {
      name: "tenant_slug",
      value: tenantSlug,
      domain: `${tenantSlug}.localhost`,
      path: "/",
      sameSite: "Lax",
    },
  ]);

  await page.goto("/dashboard");
  await page.waitForURL(/dashboard/, { timeout: 15000 });

  return {
    page,
    cleanup: () => context.close(),
  };
}

export const test = base.extend<AuthFixtures & { _freshUser: FreshUser }>({
  authenticatedPage: async ({ browser }, use) => {
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";
    const password = process.env.TEST_USER_PASSWORD || "testpassword123";
    const tenantSlug = process.env.TEST_TENANT_SLUG || "test-company";

    // Login via direct API call to get the access token
    const loginRes = await fetch(`${API_URL}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const loginData = await loginRes.json();
    if (!loginData.access) {
      throw new Error(`authenticatedPage login failed: ${JSON.stringify(loginData)}`);
    }

    const { page, cleanup } = await createTenantPage(browser, loginData.access, tenantSlug);
    await use(page);
    await cleanup();
  },

  // Internal fixture: creates the user once and shares email + token
  _freshUser: async ({}, use) => {
    const email = uniqueEmail("fresh");
    const data = await createTestUser({
      email,
      password: "TestPassword123!",
      first_name: "Fresh",
      last_name: "User",
    });
    await use({ email, token: data.access, tenantSlug: data.tenant_slug });
  },

  freshUserToken: async ({ _freshUser }, use) => {
    await use(_freshUser.token);
  },

  freshUserEmail: async ({ _freshUser }, use) => {
    await use(_freshUser.email);
  },

  freshUserPage: async ({ browser, _freshUser }, use) => {
    const { page, cleanup } = await createTenantPage(browser, _freshUser.token, _freshUser.tenantSlug);
    await use(page);
    await cleanup();
  },
});

export { expect } from "@playwright/test";
