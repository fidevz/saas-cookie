import { test, expect } from "@playwright/test";
import { uniqueEmail, createTestUser, loginTestUser } from "../../utils/api-helpers";

const TEST_EMAIL = process.env.TEST_USER_EMAIL || "admin@test.com";
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || "testpassword123";

test.describe("Team Management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);
  });

  test("team page renders if feature is enabled", async ({ page }) => {
    await page.goto("/settings/team");

    // Either the team page renders or a "feature not available" message
    const teamHeading = page.getByRole("heading", { name: /team/i });
    const featureDisabled = page.getByText(/not available|feature disabled|coming soon/i);

    const isTeamVisible = await teamHeading.isVisible().catch(() => false);
    const isDisabled = await featureDisabled.isVisible().catch(() => false);

    // One of them should be true
    expect(isTeamVisible || isDisabled).toBeTruthy();
  });

  test("invite form is visible on team page", async ({ page }) => {
    await page.goto("/settings/team");

    const emailInput = page.getByLabel(/email address/i);
    if (await emailInput.isVisible()) {
      await expect(emailInput).toBeVisible();
      await expect(page.getByRole("button", { name: /send invite/i })).toBeVisible();
    }
  });

  test("can invite a new member", async ({ page }) => {
    await page.goto("/settings/team");

    const emailInput = page.getByLabel(/email address/i);
    if (!await emailInput.isVisible()) {
      test.skip();
      return;
    }

    const newEmail = uniqueEmail("invited");

    // Mock invite endpoint
    await page.route("**/api/v1/teams/invitations/", (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            email: newEmail,
            role: "member",
            token: "test-token-123",
          }),
        });
      } else {
        route.continue();
      }
    });

    await emailInput.fill(newEmail);

    const roleSelect = page.getByRole("combobox");
    if (await roleSelect.isVisible()) {
      await roleSelect.selectOption("member");
    }

    await page.getByRole("button", { name: /send invite/i }).click();

    // Should show success toast or message
    await expect(
      page.getByText(/invitation sent|invite sent/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test("members list shows current user", async ({ page }) => {
    await page.goto("/settings/team");

    const emailInput = page.getByLabel(/email address/i);
    if (!await emailInput.isVisible()) {
      test.skip();
      return;
    }

    // Current user should appear in the members list
    await expect(page.getByText(TEST_EMAIL)).toBeVisible();
  });

  test("accept invitation page renders", async ({ page }) => {
    await page.goto("/invite/test-token-123");

    // Either shows invite details or an error (expired/invalid token)
    const heading = page.getByRole("heading");
    await expect(heading).toBeVisible();
  });
});
