import { test, expect } from "@playwright/test";

test.describe("Legal Pages", () => {
  test("Terms of Service page renders", async ({ page }) => {
    await page.goto("/legal/tos");

    await expect(page.getByRole("heading", { name: /terms of service/i })).toBeVisible();
    await expect(page.getByText(/last updated/i)).toBeVisible();
  });

  test("Privacy Policy page renders", async ({ page }) => {
    await page.goto("/legal/privacy");

    await expect(page.getByRole("heading", { name: /privacy policy/i })).toBeVisible();
    await expect(page.getByText(/last updated/i)).toBeVisible();
  });

  test("TOS page has readable content", async ({ page }) => {
    await page.goto("/legal/tos");

    // Should have paragraphs of text
    const paragraphs = page.locator("p");
    const count = await paragraphs.count();
    expect(count).toBeGreaterThan(0);
  });

  test("Privacy page has readable content", async ({ page }) => {
    await page.goto("/legal/privacy");

    const paragraphs = page.locator("p");
    const count = await paragraphs.count();
    expect(count).toBeGreaterThan(0);
  });

  test("legal pages have navigation back to home", async ({ page }) => {
    await page.goto("/legal/tos");

    // Should have a link back to home (logo or breadcrumb)
    const homeLink = page.getByRole("link", { name: /home|logo/i })
      .or(page.locator('a[href="/"]'))
      .first();

    await expect(homeLink).toBeVisible();
  });

  test("footer links to TOS and Privacy work", async ({ page }) => {
    await page.goto("/");

    const tosLink = page.getByRole("link", { name: /terms of service/i });
    await tosLink.click();
    await expect(page).toHaveURL(/legal\/tos/);
  });
});
