# Frontend — Getting Started

## Prerequisites

- Node.js 20+
- pnpm (`npm install -g pnpm`)
- A running backend at the URL in your `.env.local`

---

## 1. Installation

```bash
pnpm install
```

---

## 2. Environment

Copy the example env file and fill in your values:

```bash
cp .env.example .env.local
```

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (e.g. `http://localhost:8000/api/v1`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket server URL (e.g. `ws://localhost:8000`) |
| `NEXT_PUBLIC_APP_NAME` | Display name of your app |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth client ID |

---

## 3. Development

```bash
pnpm dev
```

App runs at http://localhost:3000.

---

## 4. Build

```bash
pnpm build
pnpm start
```

---

## 5. Lint & Type Check

```bash
pnpm lint
pnpm type-check
```

---

## 6. Internationalization (i18n)

Strings live in `messages/en.json` and `messages/es.json`. To add a new string:

1. Add the key/value to `messages/en.json`
2. Add the translated value to `messages/es.json`
3. Use with `useTranslations("namespace")` in any component

To add a new locale, update `src/i18n/routing.ts`:
```ts
locales: ["en", "es", "fr"],  // add your locale
```
Then create `messages/fr.json`.

---

## 7. Theming

Edit the CSS variables in `src/app/globals.css` to retheme the app. The `:root` block sets light mode colors and `.dark` sets dark mode. All shadcn/ui components automatically use these variables.

To change the primary brand color, update `--primary` and `--primary-foreground` in both blocks.

---

## 8. Feature Flags

Feature flags are fetched from the backend at `/api/v1/features/` and cached in Zustand. The flag keys are:

| Flag | Controls |
|---|---|
| `TEAMS` | Team management page and sidebar item |
| `BILLING` | Billing page and sidebar item |
| `NOTIFICATIONS` | Notification bell and WebSocket connection |

Flags are checked in `useFeatureStore().flags.FLAG_NAME`.

---

## 9. Stripe

1. Set `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` in `.env.local`
2. Configure your backend to handle Stripe webhooks
3. Plans are fetched from `/api/v1/billing/plans/` and displayed on the pricing page
4. Checkout sessions are created via `/api/v1/billing/checkout/`
5. Customer portal opens via `/api/v1/billing/portal/`

---

## 10. Google OAuth

1. Create a Google OAuth app at https://console.cloud.google.com
2. Set the redirect URI to `http://localhost:3000/auth/callback`
3. Set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in `.env.local`
4. Configure your backend `/api/v1/auth/google/` to return the OAuth URL

---

## Architecture Notes

- **Auth**: Access token stored in Zustand memory (never persisted). Refresh token in httpOnly cookie. On page load, `AuthInitializer` attempts a silent token refresh.
- **API client**: `src/lib/api.ts` — auto-attaches auth headers, handles 401 with refresh, extracts API error messages.
- **Route protection**: Two layers — Next.js middleware (`src/middleware.ts`) for server-side redirects, and the protected layout (`src/app/(protected)/layout.tsx`) for client-side guards.
- **Multi-tenancy**: The frontend is designed to run per-tenant on a subdomain. Tenant context is resolved server-side by the backend based on the hostname.
- **WebSocket**: Connected in the protected layout when `NOTIFICATIONS` feature flag is enabled. Reconnects automatically with exponential backoff.
