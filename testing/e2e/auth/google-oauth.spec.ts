import { test, expect } from "@playwright/test";

test.describe("Google OAuth", () => {
  test("Google button on login page redirects to Google", async ({ page }) => {
    await page.goto("/auth/login");

    // Mock the Google Auth URL endpoint to return a Google URL
    await page.route("**/api/v1/auth/google/**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ url: "https://accounts.google.com/o/oauth2/auth?mock=true" }),
      });
    });

    // Block the actual Google navigation so we stay on the test environment
    let navigationAttempted = false;
    await page.route("https://accounts.google.com/**", (route) => {
      navigationAttempted = true;
      route.abort();
    });

    await page.getByRole("button", { name: /continue with google/i }).click();

    // Wait until Google navigation is attempted (or timeout) — deterministic wait
    await page.waitForEvent("requestfailed", {
      predicate: (req) => req.url().includes("accounts.google.com"),
      timeout: 5000,
    }).catch(() => {
      // May have already fired before waitForEvent was registered
    });

    // Verify that Google OAuth redirect was attempted
    expect(navigationAttempted).toBeTruthy();
  });

  test("Google button on register page is visible", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.getByRole("button", { name: /continue with google/i })).toBeVisible();
  });

  test("OAuth callback page handles errors gracefully", async ({ page }) => {
    // Simulate a failed OAuth callback
    await page.goto("/auth/callback?error=access_denied");

    // Should redirect to login with an error message
    await page.waitForURL(/auth\/login/);
  });
});
