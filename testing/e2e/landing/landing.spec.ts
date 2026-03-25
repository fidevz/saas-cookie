import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders hero section with CTA", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: /get started|start for free/i }).first()).toBeVisible();
  });

  test("renders features section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /everything you need/i })).toBeVisible();
  });

  test("renders pricing section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /simple, transparent pricing/i })).toBeVisible();
  });

  test("navigation links work", async ({ page }) => {
    // Pricing link in nav goes to pricing page
    await page.getByRole("link", { name: /^pricing$/i }).first().click();
    await expect(page).toHaveURL(/pricing/);
  });

  test("sign in link navigates to login", async ({ page }) => {
    await page.getByRole("link", { name: /sign in/i }).click();
    await expect(page).toHaveURL(/auth\/login/);
  });

  test("get started CTA navigates to register", async ({ page }) => {
    await page.getByRole("link", { name: /get started|start for free/i }).first().click();
    await expect(page).toHaveURL(/auth\/register/);
  });

  test("footer has legal links", async ({ page }) => {
    await expect(page.getByRole("link", { name: /terms of service/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /privacy policy/i })).toBeVisible();
  });

  test("page is mobile responsive", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });
});
