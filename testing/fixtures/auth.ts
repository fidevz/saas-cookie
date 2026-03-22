import { test as base, Page } from "@playwright/test";
import { loginTestUser, uniqueEmail, createTestUser } from "../utils/api-helpers";

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

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";
    const password = process.env.TEST_USER_PASSWORD || "testpassword123";

    // Login via UI
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /sign in/i }).click();

    // Wait for redirect to dashboard
    await page.waitForURL(/dashboard/);

    await use(page);
  },

  freshUserPage: async ({ page, freshUserEmail, freshUserToken }, use) => {
    // Set the access token in the page's localStorage/Zustand via evaluate
    await page.goto("/");
    await page.evaluate((token) => {
      // Store in sessionStorage for the Zustand store to pick up
      sessionStorage.setItem("access_token", token);
    }, freshUserToken);

    // Navigate to trigger auth state
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(freshUserEmail);
    await page.getByLabel(/password/i).fill("TestPassword123!");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);

    await use(page);
  },

  freshUserToken: async ({}, use) => {
    const email = uniqueEmail("fresh");
    const data = await createTestUser({
      email,
      password: "TestPassword123!",
      first_name: "Fresh",
      last_name: "User",
    });
    await use(data.access_token);
  },

  freshUserEmail: async ({}, use) => {
    const email = uniqueEmail("fresh");
    await use(email);
  },
});

export { expect } from "@playwright/test";
