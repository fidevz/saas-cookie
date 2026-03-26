# Billing

Billing is powered by Stripe. Each tenant gets one subscription. Only tenant admins can manage billing. The feature can be toggled off entirely with `FEATURE_BILLING=false`.

---

## Table of Contents

- [Overview](#overview)
- [Data Model](#data-model)
- [API Endpoints](#api-endpoints)
- [Frontend Pages](#frontend-pages)
- [Subscription Lifecycle](#subscription-lifecycle)
- [Webhook Events](#webhook-events)
- [Paywall Middleware](#paywall-middleware)
- [Email Notifications](#email-notifications)
- [Feature Flag](#feature-flag)
- [Setup](#setup)

---

## Overview

```
User selects plan → Stripe Checkout → checkout.session.completed webhook
                                          ↓
                                   Subscription created/updated in DB
                                          ↓
                              Ongoing: invoice.paid / subscription.updated webhooks
```

Plans are stored in the database and linked to Stripe Price IDs. Each tenant has exactly one `Subscription` record (one-to-one). All mutations (checkout, cancel, portal) require `IsTenantAdmin` permission.

---

## Data Model

### Plan

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Display name, e.g. "Pro" |
| `stripe_price_id` | string | Stripe Price ID (`price_xxx`), unique, nullable for free plans |
| `stripe_product_id` | string | Stripe Product ID |
| `amount` | decimal | Price in dollars (e.g. `9.99`). Serialized as **cents** in the API. |
| `currency` | string | ISO 4217 code, default `usd` |
| `interval` | enum | `month` or `year` |
| `trial_days` | int | Free trial length, `0` = no trial |
| `is_active` | bool | Inactive plans are hidden from the API |
| `features` | JSON | Feature list — either `["Feature A", "Feature B"]` or `{"Feature A": true, "Feature B": false}` |

Plans are ordered by `amount` ascending. A plan with `amount=0` is considered free (`plan.is_free`).

### Subscription

One per tenant. Created by the checkout webhook or `SelectFreePlanView`.

| Field | Type | Notes |
|-------|------|-------|
| `tenant` | FK | One-to-one with Tenant |
| `plan` | FK | The active Plan (nullable, SET_NULL) |
| `status` | enum | See statuses below |
| `stripe_subscription_id` | string | Stripe subscription ID |
| `stripe_customer_id` | string | Stripe customer ID (reused on upgrades) |
| `current_period_start` | datetime | Current billing period start |
| `current_period_end` | datetime | Current billing period end |
| `trial_end` | datetime | When the trial expires (nullable) |
| `cancelled_at` | datetime | When the subscription was cancelled (nullable) |

#### Subscription Statuses

| Status | Meaning | `is_active` |
|--------|---------|-------------|
| `trialing` | Free trial in progress | ✅ |
| `active` | Paid and current | ✅ |
| `cancelling` | Will cancel at period end (`cancel_at_period_end=True` in Stripe) | ✅ |
| `cancelled` | Fully cancelled | ❌ |
| `past_due` | Payment failed, retry in progress | ❌ |
| `unpaid` | All retries exhausted | ❌ |

---

## API Endpoints

All endpoints are under `/api/v1/subscriptions/`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `plans/` | Public | List all active plans, ordered by price |
| `GET` | `current/` | Authenticated | Get the tenant's current subscription |
| `POST` | `checkout/` | Tenant admin | Create a Stripe Checkout session |
| `POST` | `portal/` | Tenant admin | Open Stripe Customer Portal session |
| `POST` | `cancel/` | Tenant admin | Cancel subscription at period end |
| `POST` | `select-free/` | Tenant admin | Activate the free plan (no Stripe) |
| `POST` | `webhook/` | None (Stripe signature) | Receive Stripe webhook events |

### `GET /subscriptions/plans/`

Returns all active plans. Public — no auth required (used on the landing page pricing section).

```json
[
  {
    "id": 1,
    "name": "Starter",
    "stripe_price_id": "price_xxx",
    "amount": 900,
    "currency": "usd",
    "interval": "month",
    "trial_days": 14,
    "features": ["5 users", "10GB storage"]
  }
]
```

Note: `amount` is in **cents** (serializer multiplies by 100).

### `POST /subscriptions/checkout/`

Creates a Stripe Checkout session and returns the hosted URL.

**Request:**
```json
{
  "plan_id": 2,
  "success_url": "https://tenant.yourdomain.com/billing/success",
  "cancel_url": "https://tenant.yourdomain.com/billing"
}
```

**Response:**
```json
{ "url": "https://checkout.stripe.com/...", "session_id": "cs_xxx" }
```

- Passes `client_reference_id` (tenant PK) and `metadata.plan_id` to Stripe so the webhook can look up the tenant.
- Reuses existing `stripe_customer_id` if the tenant has one, so payment methods are retained across plan switches.
- Applies `trial_period_days` if the plan has `trial_days > 0`.

### `POST /subscriptions/portal/`

Creates a Stripe Customer Portal session. The portal handles:
- Plan upgrades/downgrades (if enabled in your Stripe Dashboard → Customer Portal settings)
- Payment method updates
- Invoice history

**Response:**
```json
{ "url": "https://billing.stripe.com/..." }
```

### `POST /subscriptions/cancel/`

Cancels the Stripe subscription at period end (`cancel_at_period_end=True`). Sets local status to `cancelling`. The user retains access until `current_period_end`.

### `POST /subscriptions/select-free/`

Creates a local `Subscription` with `status=active` for the free plan. No Stripe interaction. Only works if the tenant has no existing subscription and a plan with `amount=0` exists.

---

## Frontend Pages

| Route | Component | Access |
|-------|-----------|--------|
| `/billing` | `billing/page.tsx` | Tenant admin |
| `/billing/success` | `billing/success/page.tsx` | Any authenticated |
| `/billing/cancel` | `billing/cancel/page.tsx` | Tenant admin |

### `/billing`

**No subscription:** Shows plan cards via `PlanCard`. Free plan calls `selectFreePlan()`. Paid plans call `createCheckoutSession()` and redirect to Stripe Checkout.

**Active subscription:** Shows:
- Current plan name, price, status badge, billing period dates
- "Manage subscription" button → opens Stripe Customer Portal
- "Upgrade your plan" section (if higher-tier plans exist) — each card's "Upgrade" button also opens the portal
- "Cancel subscription" link → `/billing/cancel`

**Cancelling subscription:** Hides the cancel link and upgrade section. Shows "Reactivate subscription" button → opens portal. Shows "Access until" date.

Non-admin members with an existing subscription are redirected to `/dashboard`.

### `/billing/success`

Shown after Stripe Checkout completes. Auto-redirects to `/billing` after 5 seconds.

### `/billing/cancel`

Shows a cancellation survey (`CancelSurvey` component) with 5 reason options. Calls `POST /subscriptions/cancel/` on confirm. Non-destructive — user retains access to end of period.

### Key Frontend Files

```
frontend/src/
  app/(protected)/billing/
    page.tsx              # Main billing page
    success/page.tsx      # Post-checkout confirmation
    cancel/page.tsx       # Cancellation page
  components/billing/
    plan-card.tsx         # Reusable plan card (checkout + upgrade)
    paywall.tsx           # Full-page paywall (no subscription + REQUIRE_SUBSCRIPTION on)
    subscription-status.tsx  # Status badge component
    cancel-survey.tsx     # Cancellation reason form
  hooks/use-subscription.ts  # Subscription data hook
  lib/stripe.ts           # All Stripe API call wrappers
```

---

## Subscription Lifecycle

```
[No subscription]
      │
      ├─ Selects free plan ──────────────────────► [active] (no Stripe)
      │
      └─ Selects paid plan ──► Stripe Checkout
                                      │
                         checkout.session.completed
                                      │
                                      ▼
                              [trialing] or [active]
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                   │
              invoice.paid    payment_failed    cancel_at_period_end
                    │                 │                   │
                    ▼                 ▼                   ▼
                [active]         [past_due]         [cancelling]
                                      │                   │
                                      │            (period ends)
                               (retries fail)             │
                                      │                   ▼
                                      ▼             [cancelled]
                                  [unpaid]
                                      │
                              subscription.deleted
                                      │
                                      ▼
                                [cancelled]
```

---

## Webhook Events

Stripe sends events to `POST /api/v1/subscriptions/webhook/`. The signature is verified using `STRIPE_WEBHOOK_SECRET` (skipped if not set — development only).

| Event | Handler | What it does |
|-------|---------|--------------|
| `checkout.session.completed` | `_handle_checkout_completed` | Creates/updates the Subscription record; stores Stripe IDs and period dates |
| `invoice.paid` | `_handle_invoice_paid` | Sets status → `active`; updates billing period dates |
| `invoice.payment_failed` | `_handle_invoice_payment_failed` | Sets status → `past_due`; dispatches `send_payment_failed_email` Celery task |
| `customer.subscription.updated` | `_handle_subscription_updated` | Syncs status and period dates; detects `cancel_at_period_end` → sets `cancelling` |
| `customer.subscription.deleted` | `_handle_subscription_deleted` | Sets status → `cancelled`; records `cancelled_at` timestamp |

### Stripe Status → Local Status Mapping

| Stripe `status` | `cancel_at_period_end` | Local status |
|-----------------|------------------------|--------------|
| `trialing` | any | `trialing` |
| `active` | `false` | `active` |
| `active` | `true` | `cancelling` |
| `past_due` | any | `past_due` |
| `unpaid` | any | `unpaid` |
| `canceled` | any | `cancelled` |
| `incomplete` | any | `past_due` |
| `incomplete_expired` | any | `cancelled` |

### Local Development

Use the Stripe CLI to forward webhooks to your local server:

```bash
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook/
```

Copy the displayed webhook signing secret into `STRIPE_WEBHOOK_SECRET`.

---

## Paywall Middleware

`SubscriptionPaywallMiddleware` is active when `FEATURE_REQUIRE_SUBSCRIPTION=true`. It returns **HTTP 402** for authenticated API requests from tenants without an active subscription.

**Exempt paths** (always allowed regardless of subscription):

```
/health
/api/v1/auth/
/api/v1/features/
/api/v1/subscriptions/     ← so users can subscribe
/api/v1/support/
/api/v1/users/me           ← needed for auth initialization
/api/v1/tenants/members/   ← needed for role check in layout
/api/v1/notifications/     ← needed for notification UI in layout
/api/docs/
/api/schema/
```

**Frontend paywall:** When `REQUIRE_SUBSCRIPTION` is enabled and the user has no active subscription, the protected layout renders the `Paywall` component instead of the app shell. This is a full-page takeover showing the logo, plan cards, and a logout button.

The API client (`src/lib/api.ts`) treats 402 as a non-fatal error — it throws but does not redirect, leaving the layout's paywall rendering to handle the UX.

---

## Email Notifications

Two Celery tasks handle billing emails:

### `send_trial_ending_email`

Sent to the tenant owner when their trial ends within 3 days. Triggered by the `check_trial_endings` periodic task (run daily via Celery Beat).

Templates: `backend/templates/subscriptions/email/trial_ending.{html,txt}`

### `send_payment_failed_email`

Sent to the tenant owner when `invoice.payment_failed` is received. Includes the failed charge amount. Retried up to 3 times with 5-minute delays.

Templates: `backend/templates/subscriptions/email/payment_failed.{html,txt}`

---

## Feature Flag

| Flag | Env var | Default |
|------|---------|---------|
| `BILLING` | `FEATURE_BILLING` | `true` |
| `REQUIRE_SUBSCRIPTION` | `FEATURE_REQUIRE_SUBSCRIPTION` | `false` |

- `BILLING=false` disables all billing endpoints (returns 403). Plans list remains public.
- `REQUIRE_SUBSCRIPTION=true` enables the paywall middleware and full-page paywall. Set this once you're ready to charge users.

---

## Setup

### 1. Create plans in Stripe

In your Stripe Dashboard, create Products and Prices. Copy each Price ID (`price_xxx`).

### 2. Create plans in Django admin

Go to `/admin/` → **Subscriptions → Plans** → Add Plan. Fill in the name, amount, interval, `stripe_price_id`, and features. For a free tier, set `amount=0` and leave `stripe_price_id` blank.

### 3. Configure environment variables

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 4. Configure Stripe Customer Portal

In Stripe Dashboard → Settings → Customer Portal:
- Enable "Allow customers to switch plans" to support upgrades
- Add the plans users can switch to
- Set the return URL to `https://tenant.yourdomain.com/billing/`

### 5. Register the webhook endpoint

In Stripe Dashboard → Developers → Webhooks → Add endpoint:

- URL: `https://yourdomain.com/api/v1/subscriptions/webhook/`
- Events to listen for:
  - `checkout.session.completed`
  - `invoice.paid`
  - `invoice.payment_failed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
