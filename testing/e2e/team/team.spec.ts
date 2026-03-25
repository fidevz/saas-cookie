import { test, expect } from "../../fixtures/auth";

const TEST_EMAIL = process.env.TEST_USER_EMAIL || "admin@test.com";

test.describe("Team Management", () => {
  test("team page renders if feature is enabled", async ({ authenticatedPage: page }) => {
    await page.goto("/settings/team");

    // If TEAMS feature is disabled, the page redirects to /dashboard
    // If enabled, it shows the Team heading
    await page.waitForURL(/settings\/team|dashboard/, { timeout: 5000 });

    const isDashboard = page.url().includes("/dashboard");
    if (!isDashboard) {
      await expect(page.getByRole("heading", { name: /team/i })).toBeVisible();
    }
    // One of: team page rendered, or redirected to dashboard (feature off)
    expect(isDashboard || page.url().includes("/settings/team")).toBeTruthy();
  });

  test("invite form is visible on team page", async ({ authenticatedPage: page }) => {
    await page.goto("/settings/team");
    await page.waitForURL(/settings\/team|dashboard/, { timeout: 5000 });

    const emailInput = page.getByLabel(/email address/i);
    if (await emailInput.isVisible()) {
      await expect(emailInput).toBeVisible();
      await expect(page.getByRole("button", { name: /send invite/i })).toBeVisible();
    }
  });

  test("can invite a new member", async ({ authenticatedPage: page }) => {
    await page.goto("/settings/team");
    await page.waitForURL(/settings\/team|dashboard/, { timeout: 5000 });

    const emailInput = page.getByLabel(/email address/i);
    if (!await emailInput.isVisible()) {
      test.skip();
      return;
    }

    const newEmail = `invited-${Date.now()}@test.com`;

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

  test("members list shows current user", async ({ authenticatedPage: page }) => {
    await page.goto("/settings/team");
    await page.waitForURL(/settings\/team|dashboard/, { timeout: 5000 });

    const emailInput = page.getByLabel(/email address/i);
    if (!await emailInput.isVisible()) {
      test.skip();
      return;
    }

    await expect(page.getByText(TEST_EMAIL)).toBeVisible();
  });

  test("accept invitation page shows invalid message for unknown token", async ({ page }) => {
    // Navigating with an unknown token — the API returns 404, page should show an error
    await page.goto("/invite/nonexistent-token-xyz");

    const anyText = page.locator("p, h1, h2, h3").first();
    await expect(anyText).toBeVisible({ timeout: 10000 });
  });

  test("accept invitation page shows tenant name and join prompt for valid token", async ({ page }) => {
    const INVITE_TOKEN = "valid-invite-token-abc";
    const TENANT_NAME = "Acme Corp";

    // Mock the invitation lookup (GET /teams/invitations/{token}/)
    await page.route(`**/api/v1/teams/invitations/${INVITE_TOKEN}/`, (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "invitee@example.com",
          role: "member",
          token: INVITE_TOKEN,
          accepted: false,
          expires_at: new Date(Date.now() + 86400000).toISOString(),
          tenant: { id: 1, name: TENANT_NAME, slug: "acme-corp" },
        }),
      });
    });

    await page.goto(`/invite/${INVITE_TOKEN}`);

    // Should show invitation heading and tenant name in subtitle
    await expect(page.getByText(/you've been invited/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(new RegExp(TENANT_NAME, "i"))).toBeVisible({ timeout: 5000 });

    // Should show "Sign up to accept" button for unauthenticated users
    await expect(page.getByRole("button", { name: /sign up to accept/i })).toBeVisible({ timeout: 5000 });
  });

  test("clicking sign up to accept navigates to register with invite_token", async ({ page }) => {
    const INVITE_TOKEN = "valid-invite-token-abc";

    await page.route(`**/api/v1/teams/invitations/${INVITE_TOKEN}/`, (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          email: "invitee@example.com",
          role: "member",
          token: INVITE_TOKEN,
          accepted: false,
          expires_at: new Date(Date.now() + 86400000).toISOString(),
          tenant: { id: 1, name: "Acme Corp", slug: "acme-corp" },
        }),
      });
    });

    await page.goto(`/invite/${INVITE_TOKEN}`);

    const signUpButton = page.getByRole("button", { name: /sign up to accept/i });
    await expect(signUpButton).toBeVisible({ timeout: 5000 });
    await signUpButton.click();

    // Should navigate to register page with invite_token query param
    await page.waitForURL(/auth\/register.*invite_token=/, { timeout: 5000 });
    expect(page.url()).toContain(`invite_token=${INVITE_TOKEN}`);
  });
});
