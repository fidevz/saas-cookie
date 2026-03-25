# Stripe Setup Guide

> Step-by-step to configure Stripe for a new project using this boilerplate.
> The seed command creates plans in the DB — this guide creates them in Stripe first.

---

## 1. Create a Stripe Account

Go to [dashboard.stripe.com](https://dashboard.stripe.com) and create an account or log in.

---

## 2. Get Your API Keys

In Stripe Dashboard → Developers → API keys:

| Key | Where to use |
|-----|-------------|
| **Publishable key** (`pk_test_...`) | `STRIPE_PUBLISHABLE_KEY` + `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` |
| **Secret key** (`sk_test_...`) | `STRIPE_SECRET_KEY` |

Use `pk_test_` / `sk_test_` for development. Use `pk_live_` / `sk_live_` for production.

---

## 3. Create Products and Prices

In Stripe Dashboard → Product catalog → Add product:

### Starter Plan
- **Name:** Starter
- **Pricing:** $9.00 / month (recurring)
- **Copy the Price ID:** `price_xxxxx` → you'll need this

### Pro Plan
- **Name:** Pro
- **Pricing:** $29.00 / month (recurring)
- **Enable free trial:** 14 days
- **Copy the Price ID:** `price_xxxxx` → you'll need this

> You can also add annual pricing variants for each plan.

---

## 4. Update the Seed Command

Open `backend/apps/subscriptions/management/commands/seed.py` (or wherever seed data is defined) and update the `stripe_price_id` values to match your newly created Price IDs:

```python
Plan.objects.get_or_create(
    name="Starter",
    defaults={
        "amount": 900,          # in cents
        "currency": "usd",
        "interval": "month",
        "stripe_price_id": "price_XXXXXXXXXXXXXXXX",  # ← your Price ID
        "trial_days": 0,
    }
)

Plan.objects.get_or_create(
    name="Pro",
    defaults={
        "amount": 2900,
        "currency": "usd",
        "interval": "month",
        "stripe_price_id": "price_XXXXXXXXXXXXXXXX",  # ← your Price ID
        "trial_days": 14,
    }
)
```

Then run:
```bash
make db-reset  # or just: uv run python manage.py seed
```

---

## 5. Configure the Webhook

### Local Development (Stripe CLI)

Install the [Stripe CLI](https://stripe.com/docs/stripe-cli):
```bash
brew install stripe/stripe-cli/stripe
stripe login
```

Forward events to your local server:
```bash
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook/
```

Copy the webhook signing secret printed in the terminal:
```
> Ready! Your webhook signing secret is whsec_xxxxx (^C to quit)
```

Set it in `backend/.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### Production

In Stripe Dashboard → Developers → Webhooks → Add endpoint:

- **URL:** `https://api.yourdomain.com/api/v1/subscriptions/webhook/`
- **Events to listen to:**
  - `checkout.session.completed`
  - `invoice.paid`
  - `invoice.payment_failed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`

Copy the **Signing secret** and set `STRIPE_WEBHOOK_SECRET` in your production environment.

---

## 6. Test the Integration

Use Stripe's test card numbers:

| Scenario | Card number | Notes |
|----------|------------|-------|
| Successful payment | `4242 4242 4242 4242` | Any future expiry, any CVC |
| Payment requires auth | `4000 0025 0000 3155` | 3D Secure |
| Payment declined | `4000 0000 0000 9995` | Insufficient funds |
| Dispute (chargeback) | `4000 0000 0000 0259` | — |

Test the full flow:
1. Sign up at `http://localhost:3000`
2. Go to Billing → choose a plan
3. Complete checkout with test card `4242 4242 4242 4242`
4. Verify subscription is created in Stripe Dashboard
5. Verify webhook was received (check terminal running `stripe listen`)
6. Verify subscription status updated in Django admin at `http://localhost:8000/tacomate/`

---

## 7. Customer Portal

The Customer Portal lets users manage their subscription (update card, cancel, etc.) without custom UI.

Enable it in Stripe Dashboard → Settings → Billing → Customer portal:
- Allow customers to update payment methods: ✅
- Allow customers to cancel subscriptions: ✅
- Configure cancellation flow (collect reason): ✅

The boilerplate's `/api/v1/subscriptions/portal/` endpoint creates a portal session and redirects the user.

---

## 8. Going Live Checklist

Before switching to live keys:
- [ ] All test payments verified end-to-end
- [ ] Webhook endpoint registered for production domain with live signing secret
- [ ] `STRIPE_SECRET_KEY` set to `sk_live_...`
- [ ] `STRIPE_PUBLISHABLE_KEY` set to `pk_live_...`
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` set to `pk_live_...`
- [ ] Plans created in live mode (separate from test mode)
- [ ] Seed updated with live Price IDs
- [ ] Stripe email notifications configured (Stripe Dashboard → Settings → Emails)
- [ ] Tax settings configured if required (Stripe Tax)
