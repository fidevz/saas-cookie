# Architecture

> High-level overview of how the system is structured and why key decisions were made.

---

## System Overview

```
                        ┌─────────────────┐
                        │   Cloudflare    │  DNS + CDN + DDoS protection
                        └────────┬────────┘
               ┌─────────────────┼──────────────────┐
               ▼                 ▼                  ▼
    ┌──────────────────┐  ┌────────────┐  ┌──────────────────┐
    │  Next.js 15      │  │  Django    │  │  Django Channels │
    │  (Vercel)        │  │  REST API  │  │  WebSocket       │
    │  yourdomain.com  │  │  (ASGI)    │  │  (same process)  │
    └──────────────────┘  └─────┬──────┘  └────────┬─────────┘
                                │                   │
               ┌────────────────┼───────────────────┘
               ▼                ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  PostgreSQL  │   │    Redis     │   │  Celery      │
    │  (primary DB)│   │  (cache +    │   │  (async      │
    │              │   │   channels + │   │   tasks)     │
    │              │   │   broker)    │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## Request Flow

### HTTP Request
```
Browser → Cloudflare → Next.js (frontend)
                     → Django API (backend)
                           → TenantMiddleware (resolve tenant from subdomain)
                           → JWT Authentication
                           → View → Serializer → DB
                           → Response
```

### WebSocket Connection
```
Browser → ws://api.domain/ws/ → Django Channels (ASGI)
                              → JWT Authentication (on connect)
                              → Consumer → Channel Layer (Redis)
                              → Celery sends message to channel
                              → Consumer pushes to browser
```

### Async Task
```
View → Celery.delay() → Redis (broker) → Celery Worker → Task executes
                                                        → Result to Redis
                                                        → Optionally: WebSocket notification
```

---

## Multi-Tenancy

**Pattern:** Subdomain-based tenancy

```
yourdomain.com          → root domain (marketing, auth)
acme.yourdomain.com     → tenant "acme"
globex.yourdomain.com   → tenant "globex"
```

**How it works:**
1. `TenantMiddleware` reads the `Host` header on every request
2. Extracts subdomain, looks up `Tenant` in DB
3. Sets `request.tenant` — available in all views
4. Views use `TenantMixin` to filter data by tenant

**What is NOT tenant-scoped:**
- Admin panel (`/tacomate/`)
- API docs (`/api/docs/`)
- Health check (`/health/`)

**Tenant isolation rule:** Every queryset that returns user data must filter by `request.tenant`. This is enforced via `TenantMixin`.

---

## Authentication Flow

```
1. User registers or logs in
   → dj-rest-auth + django-allauth handle the flow
   → Returns: access_token (JSON) + sets refresh_token cookie (HttpOnly)

2. Frontend stores access_token in memory (NOT localStorage)
   → Attached to API requests as: Authorization: Bearer <token>

3. Access token expires in 5 minutes
   → Frontend silently calls /api/v1/auth/token/refresh/
   → Sends refresh_token cookie automatically (HttpOnly)
   → Gets new access_token

4. Refresh token expires in 7 days
   → User must log in again
   → Old refresh token is blacklisted on rotation (prevents reuse)
```

**Google OAuth:**
```
Frontend → Google → redirect with code → backend /api/v1/auth/google/
→ allauth exchanges code for Google profile
→ Creates/updates user → returns same JWT flow as above
```

---

## Feature Flags

Feature flags control which major modules are active:

```python
FEATURE_FLAGS = {
    "TEAMS": True,
    "BILLING": True,
    "NOTIFICATIONS": True,
}
```

- **Backend:** `FeatureFlags.teams_enabled()` — reads from settings
- **Frontend:** `useFeatureStore()` — synced from `/api/v1/core/features/` on app load
- **Changing at runtime:** update env var → restart server (flags are not DB-stored)

Use flags to ship features behind a switch, do gradual rollouts, or A/B test major UI changes.

---

## Email Architecture

All emails go through a custom Django email backend (`utils/email.py`) that delegates to **Resend**'s API.

```
Django send_mail() → ResendEmailBackend → Resend API → User inbox
```

Transactional emails (password reset, welcome) are sent inline or via Celery task depending on urgency.

---

## Subscription / Billing Flow

```
User clicks upgrade
  → Frontend creates Stripe Checkout Session (via backend API)
  → User completes payment on Stripe-hosted page
  → Stripe webhook → /api/v1/subscriptions/webhook/
  → Backend verifies signature (STRIPE_WEBHOOK_SECRET)
  → Updates Subscription model based on event type:
      checkout.session.completed → create subscription
      customer.subscription.updated → update plan
      customer.subscription.deleted → cancel subscription
      invoice.payment_failed → mark payment failed, start dunning
```

Subscription state is always driven by Stripe webhooks — never trust the frontend.

---

## Key Design Decisions

### Why ASGI (not WSGI)?
WebSockets require an async server. Daphne/ASGI handles both HTTP and WebSocket connections in a single process.

### Why Django Channels over a separate WebSocket service?
Simpler deployment. Channels integrates natively with Django's auth and ORM. At scale, a dedicated WebSocket service (e.g. Soketi) would be considered.

### Why SimpleJWT with HttpOnly cookies (not localStorage)?
HttpOnly cookies prevent XSS-based token theft. localStorage is vulnerable to any script on the page.

### Why uv instead of pip/poetry?
Significantly faster dependency resolution and installation. Lock file format is reliable. Drop-in replacement for pip workflows.

### Why Resend instead of SendGrid/Postmark?
Better developer experience, simpler API, competitive pricing, and reliable deliverability. Custom Django backend means swapping providers is a one-file change.

### Why subdomain-based tenancy instead of path-based?
Cleaner separation, enables custom domains per tenant in the future, and aligns with industry standard (Slack, Notion, etc.).
