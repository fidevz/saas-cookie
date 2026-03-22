# Testing — E2E with Playwright

End-to-end tests for the SaaS boilerplate using Playwright.

## Prerequisites

- Node.js 20+
- pnpm
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Seed data created (`make seed` in backend)

## Setup

```bash
pnpm install
pnpm run install:browsers   # Downloads Chromium
cp .env.example .env        # Configure test credentials
```

## Running Tests

```bash
# Run all tests (headless)
pnpm test

# Run with UI (interactive)
pnpm test:ui

# Run specific spec file
pnpm test e2e/auth/login.spec.ts

# Debug mode
pnpm test:debug

# See last report
pnpm report
```

## Test Structure

```
e2e/
├── auth/          # Register, login, logout, forgot password, OAuth
├── landing/       # Landing page sections and navigation
├── pricing/       # Pricing page and plan toggle
├── billing/       # Checkout flow and cancellation
├── dashboard/     # Authenticated dashboard
├── team/          # Team management (feature flagged)
├── notifications/ # WebSocket notifications
├── legal/         # TOS and Privacy pages
└── support/       # Support contact form

fixtures/
└── auth.ts        # Reusable authenticated page fixtures

utils/
└── api-helpers.ts # Create test data directly via API
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `BASE_URL` | Frontend URL | `http://localhost:3000` |
| `API_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `TEST_USER_EMAIL` | Seeded test user email | `admin@test.com` |
| `TEST_USER_PASSWORD` | Seeded test user password | `testpassword123` |
| `TEST_TENANT_SLUG` | Seeded tenant slug | `test-company` |

## Writing New Tests

1. Create a `.spec.ts` file in the appropriate `e2e/` subdirectory
2. Import from `@playwright/test`
3. Use `api-helpers.ts` for test data setup (avoid UI for setup)
4. Use the `auth.ts` fixture for authenticated tests

```typescript
import { test, expect } from "@playwright/test";

test("my feature works", async ({ page }) => {
  await page.goto("/my-page");
  await expect(page.getByRole("heading")).toBeVisible();
});
```

## CI Integration

Tests run automatically in GitHub Actions on push to main. See `.github/workflows/` for configuration.

## Tips

- Feature-flagged features (teams, notifications) use conditional logic — tests skip gracefully if feature is disabled
- Use `page.route()` to mock API calls and avoid real Stripe/email charges
- `uniqueEmail()` helper prevents test conflicts when creating users
