import { test, expect } from "@playwright/test";

const TEST_EMAIL = process.env.TEST_USER_EMAIL || "admin@test.com";
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD || "testpassword123";

test.describe("Logout", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    await page.getByLabel(/password/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/dashboard/);
  });

  test("user can log out via user menu", async ({ page }) => {
    // Open user dropdown
    const userMenu = page.getByRole("button", { name: /user menu|profile|avatar/i });
    await userMenu.click();

    await page.getByRole("menuitem", { name: /sign out|logout/i }).click();

    // Should redirect to landing or login page
    await expect(page).toHaveURL(/\/$|\/auth\/login/);
  });

  test("cannot access protected route after logout", async ({ page }) => {
    // Logout
    const userMenu = page.getByRole("button", { name: /user menu|profile|avatar/i });
    await userMenu.click();
    await page.getByRole("menuitem", { name: /sign out|logout/i }).click();
    await page.waitForURL(/\/$|\/auth\/login/);

    // Try to access dashboard
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/auth\/login/);
  });
});
