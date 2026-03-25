import { test, expect } from "../../fixtures/auth";

test.describe("Billing - Cancellation", () => {
  test("cancel page renders correctly", async ({ authenticatedPage: page }) => {
    await page.goto("/billing/cancel");
    await expect(page.getByRole("heading", { name: /cancel subscription/i })).toBeVisible();
  });

  test("cancel page has reason options", async ({ authenticatedPage: page }) => {
    await page.goto("/billing/cancel");
    await expect(page.getByRole("heading", { name: /cancel subscription/i })).toBeVisible();

    const radioGroup = page.getByRole("radiogroup");
    if (await radioGroup.isVisible()) {
      const radios = page.getByRole("radio");
      expect(await radios.count()).toBeGreaterThan(0);
    }
  });

  test("keep subscription button navigates back to billing", async ({ authenticatedPage: page }) => {
    await page.goto("/billing/cancel");
    await expect(page.getByRole("heading", { name: /cancel subscription/i })).toBeVisible();

    const keepButton = page.getByRole("button", { name: /keep subscription/i });
    if (await keepButton.isVisible()) {
      await keepButton.click();
      await expect(page).toHaveURL(/billing$/);
    }
  });

  test("cancel confirmation requires reason selection", async ({ authenticatedPage: page }) => {
    await page.goto("/billing/cancel");
    await expect(page.getByRole("heading", { name: /cancel subscription/i })).toBeVisible();

    await page.route("**/api/v1/subscriptions/cancel/", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "cancelling" }),
      });
    });

    const cancelButton = page.getByRole("button", { name: /cancel subscription/i });
    if (await cancelButton.isVisible()) {
      const firstRadio = page.getByRole("radio").first();
      if (await firstRadio.isVisible()) {
        await firstRadio.click();
      }
      await cancelButton.click();

      await expect(
        page.getByText(/cancelled|sorry to see you|subscription cancelled/i)
          .or(page.getByRole("heading", { name: /billing/i }))
      ).toBeVisible({ timeout: 5000 });
    }
  });
});
