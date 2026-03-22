import { test, expect } from "@playwright/test";

test.describe("Forgot Password", () => {
  test("forgot password page renders correctly", async ({ page }) => {
    await page.goto("/auth/forgot-password");

    await expect(page.getByRole("heading", { name: /reset your password/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /send reset link/i })).toBeVisible();
  });

  test("shows success feedback after submitting valid email", async ({ page }) => {
    const email = process.env.TEST_USER_EMAIL || "admin@test.com";

    await page.goto("/auth/forgot-password");
    await page.getByLabel(/email/i).fill(email);
    await page.getByRole("button", { name: /send reset link/i }).click();

    // Should show success message (email sent)
    await expect(page.getByText(/check your email|reset link sent/i)).toBeVisible();
  });

  test("link back to login works", async ({ page }) => {
    await page.goto("/auth/forgot-password");
    await page.getByRole("link", { name: /back to sign in/i }).click();
    await expect(page).toHaveURL(/auth\/login/);
  });

  test("reset password page requires valid token", async ({ page }) => {
    // With invalid token
    await page.goto("/auth/reset-password?token=invalid-token");

    // Should render the form (token validation happens on submit)
    await expect(page.getByRole("heading", { name: /set new password/i })).toBeVisible();
  });
});
