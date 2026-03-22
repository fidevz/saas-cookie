import { test, expect } from "@playwright/test";
import { uniqueEmail } from "../../utils/api-helpers";

test.describe("Registration", () => {
  test("user can register with email and password", async ({ page }) => {
    const email = uniqueEmail("register");

    await page.goto("/auth/register");

    await expect(page.getByRole("heading", { name: /create your account/i })).toBeVisible();

    await page.getByLabel(/first name/i).fill("Jane");
    await page.getByLabel(/last name/i).fill("Doe");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill("SecurePassword123!");

    // Accept TOS if checkbox exists
    const tosCheckbox = page.getByRole("checkbox");
    if (await tosCheckbox.isVisible()) {
      await tosCheckbox.check();
    }

    await page.getByRole("button", { name: /create account/i }).click();

    // Should redirect to dashboard after successful registration
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByText(/welcome/i)).toBeVisible();
  });

  test("shows validation errors for empty fields", async ({ page }) => {
    await page.goto("/auth/register");
    await page.getByRole("button", { name: /create account/i }).click();

    // Should show validation errors
    await expect(page.getByText(/email/i)).toBeVisible();
  });

  test("shows error for duplicate email", async ({ page }) => {
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";

    await page.goto("/auth/register");
    await page.getByLabel(/first name/i).fill("Test");
    await page.getByLabel(/last name/i).fill("User");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill("TestPassword123!");

    const tosCheckbox = page.getByRole("checkbox");
    if (await tosCheckbox.isVisible()) {
      await tosCheckbox.check();
    }

    await page.getByRole("button", { name: /create account/i }).click();

    // Should show error about existing account
    await expect(page.getByText(/already exists|already registered/i)).toBeVisible();
  });

  test("Google OAuth button is visible", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.getByRole("button", { name: /google/i })).toBeVisible();
  });

  test("redirects to dashboard if already authenticated", async ({ page }) => {
    // Login first
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";
    const password = process.env.TEST_USER_PASSWORD || "testpassword123";

    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);

    // Try to visit register page
    await page.goto("/auth/register");
    await expect(page).toHaveURL(/dashboard/);
  });
});
