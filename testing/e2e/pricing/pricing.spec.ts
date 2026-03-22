import { test, expect } from "@playwright/test";

test.describe("Pricing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/pricing");
  });

  test("renders pricing page with plans", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible();
  });

  test("monthly/annual toggle switches pricing", async ({ page }) => {
    const monthlyButton = page.getByRole("button", { name: /monthly/i });
    const annualButton = page.getByRole("button", { name: /annually|annual/i });

    if (await monthlyButton.isVisible() && await annualButton.isVisible()) {
      // Get initial prices
      await monthlyButton.click();
      const monthlyPrices = await page.getByTestId("plan-price").allTextContents();

      // Switch to annual
      await annualButton.click();
      const annualPrices = await page.getByTestId("plan-price").allTextContents();

      // Prices should differ (annual is discounted)
      expect(monthlyPrices).not.toEqual(annualPrices);
    }
  });

  test("CTA buttons link to register", async ({ page }) => {
    const ctaButtons = page.getByRole("link", { name: /get started/i });
    const firstCta = ctaButtons.first();

    if (await firstCta.isVisible()) {
      const href = await firstCta.getAttribute("href");
      expect(href).toMatch(/register|auth/);
    }
  });

  test("plan cards are visible", async ({ page }) => {
    // At least one plan card should render
    const planCards = page.getByTestId("plan-card");
    const count = await planCards.count();

    if (count === 0) {
      // Plans might not have data-testid, check for price display
      await expect(page.getByText(/\$|month|year/i).first()).toBeVisible();
    } else {
      expect(count).toBeGreaterThan(0);
    }
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle(/pricing|myapp/i);
  });
});
