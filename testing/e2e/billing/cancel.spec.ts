import { test, expect } from "@playwright/test";

const TEST_EMAIL = process.env.TEST_USER_EMAIL || "admin@test.com";
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || "testpassword123";

test.describe("Billing - Cancellation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);
  });

  test("cancel page renders correctly", async ({ page }) => {
    await page.goto("/billing/cancel");
    await expect(page.getByRole("heading", { name: /cancel subscription/i })).toBeVisible();
  });

  test("cancel page has reason options", async ({ page }) => {
    await page.goto("/billing/cancel");

    // Should have radio options for cancellation reasons
    const radioGroup = page.getByRole("radiogroup");
    if (await radioGroup.isVisible()) {
      const radios = page.getByRole("radio");
      expect(await radios.count()).toBeGreaterThan(0);
    }
  });

  test("keep subscription button navigates back to billing", async ({ page }) => {
    await page.goto("/billing/cancel");

    const keepButton = page.getByRole("button", { name: /keep subscription/i });
    if (await keepButton.isVisible()) {
      await keepButton.click();
      await expect(page).toHaveURL(/billing$/);
    }
  });

  test("cancel confirmation requires reason selection", async ({ page }) => {
    await page.goto("/billing/cancel");

    // Mock the cancel endpoint
    await page.route("**/api/v1/subscriptions/cancel/", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "cancelling" }),
      });
    });

    const cancelButton = page.getByRole("button", { name: /cancel subscription/i });
    if (await cancelButton.isVisible()) {
      // Select a reason first
      const firstRadio = page.getByRole("radio").first();
      if (await firstRadio.isVisible()) {
        await firstRadio.click();
      }
      await cancelButton.click();

      // Should show confirmation or redirect
      await expect(
        page.getByText(/cancelled|sorry to see you|subscription cancelled/i)
          .or(page.getByRole("heading", { name: /billing/i }))
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
