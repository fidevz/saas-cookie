import { test, expect } from "@playwright/test";

test.describe("Support Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/support");
  });

  test("support page renders with contact form", async ({ page }) => {
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/message/i)).toBeVisible();
  });

  test("form fields are present", async ({ page }) => {
    const emailField = page.getByLabel(/email/i);
    const messageField = page.getByLabel(/message/i);

    await expect(emailField).toBeVisible();
    await expect(messageField).toBeVisible();
  });

  test("submitting the form shows success feedback", async ({ page }) => {
    // Mock the support API endpoint
    await page.route("**/support/**", (route) => {
      route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    });

    // Fill all required fields
    await page.getByLabel(/your name|name/i).first().fill("Test User");
    await page.getByLabel(/email/i).fill("test@example.com");
    await page.getByLabel(/subject/i).fill("Test subject");
    await page.getByLabel(/message/i).fill("This is a test message from Playwright.");

    await page.getByRole("button", { name: /send message|submit/i }).click();

    // Should show success state — "Message received!" heading
    await expect(
      page.getByRole("heading", { name: /message received/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test("empty form shows validation", async ({ page }) => {
    await page.getByRole("button", { name: /send message|submit/i }).click();
    // Should still be on support page (not submitted)
    await expect(page).toHaveURL(/support/);
  });
});
