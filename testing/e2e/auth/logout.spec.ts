import { test, expect } from "../../fixtures/auth";

test.describe("Logout", () => {
  test("user can log out via user menu", async ({ authenticatedPage: page }) => {
    await page.getByRole("button", { name: /user menu/i }).click();
    await page.getByRole("menuitem", { name: /sign out/i }).click();

    await expect(page).toHaveURL(/\/$|\/auth\/login/);
  });

  test("cannot access protected route after logout", async ({ authenticatedPage: page }) => {
    await page.getByRole("button", { name: /user menu/i }).click();
    await page.getByRole("menuitem", { name: /sign out/i }).click();
    await page.waitForURL(/\/$|\/auth\/login/);

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/auth\/login/);
  });
});
