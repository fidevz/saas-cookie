import { test, expect } from "../../fixtures/auth";

// Billing page is admin-only — non-admins are redirected to /dashboard.
// The authenticatedPage fixture uses the default admin test user.

test.describe("Billing - Checkout", () => {
  test("billing page renders with subscription info", async ({ authenticatedPage: page }) => {
    await page.goto("/billing");
    await expect(page.getByRole("heading", { name: /billing/i })).toBeVisible();
  });


});
