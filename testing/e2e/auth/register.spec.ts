import { test, expect } from "@playwright/test";

test.describe("Registration", () => {
  test("shows validation errors for empty fields", async ({ page }) => {
    await page.goto("/auth/register");
    await page.getByRole("button", { name: /create account/i }).click();

    // Should show validation errors
    await expect(page.getByText(/email/i)).toBeVisible();
  });

  test("shows error for duplicate email", async ({ page }) => {
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";

    await page.goto("/auth/register");

    // Mock slug availability check
    await page.route("**/api/v1/auth/check-slug/**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ available: true }),
      });
    });

    await page.getByLabel(/workspace name/i).fill("Duplicate Test");
    await page.waitForTimeout(600);

    await page.getByLabel(/first name/i).fill("Test");
    await page.getByLabel(/last name/i).fill("User");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill("TestPassword123!");

    const tosCheckbox = page.getByRole("checkbox");
    if (await tosCheckbox.isVisible()) {
      await tosCheckbox.check();
    }

    await page.getByRole("button", { name: /create account/i }).click();

    // Should show error about existing account
    await expect(page.getByText(/already exists|already registered/i)).toBeVisible();
  });

  test("Google OAuth button is visible on standard register", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.getByRole("button", { name: /google/i })).toBeVisible();
  });

  test("redirects to dashboard if already authenticated", async ({ page }) => {
    // Login first
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";
    const password = process.env.TEST_USER_PASSWORD || "testpassword123";

    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);

    // Try to visit register page
    await page.goto("/auth/register");
    await expect(page).toHaveURL(/dashboard/);
  });

  test.describe("Invite registration flow", () => {
    const INVITE_TOKEN = "test-invite-token-abc";
    const INVITE_EMAIL = "invitee@example.com";
    const TENANT_NAME = "Acme Corp";

    test.beforeEach(async ({ page }) => {
      // Mock the invitation lookup endpoint
      await page.route(`**/api/v1/teams/invitations/${INVITE_TOKEN}/`, (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            email: INVITE_EMAIL,
            role: "member",
            token: INVITE_TOKEN,
            tenant: { id: 1, name: TENANT_NAME, slug: "acme-corp" },
          }),
        });
      });
    });

    test("shows tenant banner and no workspace fields when invite token present", async ({ page }) => {
      await page.goto(`/auth/register?invite_token=${INVITE_TOKEN}`);

      // Should show "joining" banner
      await expect(page.getByText(new RegExp(TENANT_NAME, "i"))).toBeVisible({ timeout: 5000 });

      // Workspace name and URL fields should NOT be visible
      await expect(page.getByLabel(/workspace name/i)).not.toBeVisible();
      await expect(page.getByLabel(/workspace url/i)).not.toBeVisible();
    });

    test("email is pre-filled and readonly when invite token present", async ({ page }) => {
      await page.goto(`/auth/register?invite_token=${INVITE_TOKEN}`);

      await page.waitForTimeout(500); // wait for invitation fetch

      const emailInput = page.getByLabel(/email/i);
      await expect(emailInput).toHaveValue(INVITE_EMAIL);
      await expect(emailInput).toHaveAttribute("readonly");
    });

    test("Google OAuth button is hidden when invite token present", async ({ page }) => {
      await page.goto(`/auth/register?invite_token=${INVITE_TOKEN}`);

      // Google button should not be visible in invite flow
      await expect(page.getByRole("button", { name: /google/i })).not.toBeVisible();
    });
  });
});
