import { test, expect } from "@playwright/test";

const TEST_EMAIL = process.env.TEST_USER_EMAIL || "admin@test.com";
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || "testpassword123";

test.describe("Login", () => {
  test("user can log in with valid credentials", async ({ page }) => {
    await page.goto("/auth/login");

    await expect(page.getByRole("heading", { name: /welcome back/i })).toBeVisible();

    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page).toHaveURL(/dashboard/);
  });

  test("shows error for invalid credentials", async ({ page }) => {
    await page.goto("/auth/login");

    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByText(/invalid|incorrect|wrong/i)).toBeVisible();
    await expect(page).toHaveURL(/login/);
  });

  test("shows validation error for empty email", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByLabel(/password/i).fill("somepassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page).toHaveURL(/login/);
  });

  test("forgot password link is visible", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.getByRole("link", { name: /forgot password/i })).toBeVisible();
  });

  test("link to register page works", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByRole("link", { name: /sign up/i }).click();
    await expect(page).toHaveURL(/register/);
  });

  test("Google OAuth button is visible", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.getByRole("button", { name: /google/i })).toBeVisible();
  });
});
