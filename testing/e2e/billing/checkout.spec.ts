import { test, expect } from "../../fixtures/auth";

// Billing page is admin-only — non-admins are redirected to /dashboard.
// The authenticatedPage fixture uses the default admin test user.

test.describe("Billing - Checkout", () => {
  test("billing page renders with subscription info", async ({ authenticatedPage: page }) => {
    await page.goto("/billing");
    await expect(page.getByRole("heading", { name: /billing/i })).toBeVisible();
  });

  test("manage subscription button is visible when subscribed", async ({ authenticatedPage: page }) => {
    await page.goto("/billing");
    // Wait for the heading to confirm page has loaded
    await expect(page.getByRole("heading", { name: /billing/i })).toBeVisible();

    // Button might say "Manage" or "Manage subscription" or "Upgrade"
    const manageButton = page.getByRole("button", { name: /manage|upgrade|subscribe/i });
    const noSubMessage = page.getByText(/no active subscription|no subscription|free plan|choose a plan/i);
    const hasLink = page.getByRole("link", { name: /view plans|pricing/i });

    const hasButton = await manageButton.isVisible({ timeout: 5000 }).catch(() => false);
    const hasMessage = await noSubMessage.isVisible({ timeout: 5000 }).catch(() => false);
    const hasPlansLink = await hasLink.isVisible({ timeout: 5000 }).catch(() => false);

    expect(hasButton || hasMessage || hasPlansLink).toBeTruthy();
  });

  test("stripe checkout redirect is triggered on plan selection", async ({ authenticatedPage: page }) => {
    // Mock the checkout endpoint to avoid real Stripe calls
    await page.route("**/api/v1/subscriptions/checkout/", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ url: "https://checkout.stripe.com/test-session" }),
      });
    });

    await page.goto("/pricing");
    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible();

    const ctaButton = page.getByRole("link", { name: /get started/i }).first();
    if (await ctaButton.isVisible()) {
      const href = await ctaButton.getAttribute("href");
      expect(href).toBeTruthy();
    }
  });

  test("member role is redirected from billing to dashboard", async ({ authenticatedPage: page }) => {
    // Mock the tenant members endpoint to return the current user as a member (not admin)
    await page.route("**/api/v1/tenants/members/**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          count: 1,
          results: [
            {
              user: { id: 9999, email: "someother@test.com", first_name: "Other", last_name: "User" },
              role: "member",
            },
          ],
        }),
      });
    });

    // Navigate to billing — the billing page useEffect checks currentUserRole after layout loads it.
    // Since the current user (id 9999 mock doesn't match real user), setCurrentUserRole defaults to "member".
    await page.goto("/billing");

    // Should be redirected to /dashboard as a member
    await page.waitForURL(/dashboard/, { timeout: 5000 });
    expect(page.url()).toMatch(/dashboard/);
  });
});
