import { test, expect } from "@playwright/test";

test.describe("Support Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/support");
  });

  test("support page renders with contact form", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /support|contact|help/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/message/i)).toBeVisible();
  });

  test("form fields are present", async ({ page }) => {
    const emailField = page.getByLabel(/email/i);
    const messageField = page.getByLabel(/message/i);
    const subjectField = page.getByLabel(/subject/i);

    await expect(emailField).toBeVisible();
    await expect(messageField).toBeVisible();
  });

  test("submitting the form shows success feedback", async ({ page }) => {
    // Mock any backend call
    await page.route("**/api/**", (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
      } else {
        route.continue();
      }
    });

    const nameField = page.getByLabel(/your name|name/i).first();
    if (await nameField.isVisible()) {
      await nameField.fill("Test User");
    }

    await page.getByLabel(/email/i).fill("test@example.com");

    const subjectField = page.getByLabel(/subject/i);
    if (await subjectField.isVisible()) {
      await subjectField.fill("Test subject");
    }

    await page.getByLabel(/message/i).fill("This is a test message from Playwright.");

    await page.getByRole("button", { name: /send message|submit/i }).click();

    // Should show success toast or message
    await expect(
      page.getByText(/message sent|thank you|we'll get back/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test("empty form shows validation", async ({ page }) => {
    await page.getByRole("button", { name: /send message|submit/i }).click();
    // Should still be on support page (not submitted)
    await expect(page).toHaveURL(/support/);
  });
});
