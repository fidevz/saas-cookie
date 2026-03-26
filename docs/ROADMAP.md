# Roadmap

Features and improvements identified for future development. Items are roughly ordered by priority/dependency, not by schedule.

---

## Features

### Usage Enforcement
The `team_members` integer capability is already defined in `apps/subscriptions/capabilities.py` and snapshotted on each subscription. What's missing is enforcement: `InviteMemberView` and `AcceptInviteView` in `apps/teams/views.py` never read this value before allowing a new member in.

**What to build:** Before creating an invitation (and before accepting one), fetch the tenant's active subscription capabilities, compare `team_members` against the current member count, and return a 403 if the limit is exceeded. `None` means unlimited. As new per-plan limits are added to the registry, the same pattern applies.

---

### API Keys
Allow users to authenticate programmatically without going through the browser login flow. Useful for CLI tools, integrations, and webhooks sent by the user's own systems.

**What to build:** An `APIKey` model (hashed key, name, last used, scopes, expiry). A DRF authentication backend that accepts `Authorization: Bearer sk_...` tokens. A UI in Settings to create and revoke keys.

---

### Audit Log
A record of significant actions taken within a tenant — who did what, when, and on which resource. Often required for compliance (SOC 2, HIPAA) and useful for support debugging.

**What to build:** A generic `AuditLog` model: `(user, action, resource_type, resource_id, metadata JSON, ip, timestamp)`. A reusable `audit()` helper function to call from views. Apps that need detailed logging opt in; no strict schema required. Expose a read-only list view in the admin and optionally in the tenant settings.

---

### Onboarding Flow
A post-signup checklist or wizard that guides new users to their first "aha moment". Increases activation rates significantly.

**What to build:** A `CompletedStep` model tied to user/tenant with a fixed set of step keys (`invite_member`, `complete_profile`, `setup_billing`, etc.). A dismissible checklist component on the dashboard. Step definitions are project-specific but the infrastructure is generic.

---

### Admin Impersonation
Allow support staff to log in as any user to debug their account without knowing their password.

**What to build:** A Django admin action that generates a short-lived impersonation token. A view that exchanges it for a real session. Log all impersonation events to the audit log. Impersonated sessions should be clearly marked in the UI.

---

### In-app Changelog / Announcements
A "What's new" panel to announce features, fixes, and updates inside the app. Drives awareness of new features and reduces churn.

**What to build:** An `Announcement` model managed via the Django admin (title, body, published date, audience targeting). Delivered via the existing notifications infrastructure or a dedicated "changelog" dropdown. Badge on the bell or a dedicated icon until dismissed.

---

### Data Export
Let users download all their data in a machine-readable format. Required for GDPR compliance and expected by enterprise buyers.

**What to build:** A Celery task that serializes all user/tenant data to CSV or JSON, uploads to S3/MinIO, and emails a download link. A "Request export" button in Settings. Exported files expire after 7 days.

---

### SSO / SAML
Let companies authenticate via their own identity provider (Okta, Azure AD, Google Workspace) instead of managing passwords. Table stakes for enterprise deals.

**What to build:** A `SAMLConfig` model per tenant storing IdP metadata URL and certificates. `django-saml2-auth` handles the assertion flow. Login page detects tenant subdomain and shows "Sign in with SSO" when a config exists.

---

## Risks

### 1. WebSocket Token in Query String
The JWT access token is passed as `?token=` in the WebSocket URL (`ws.ts`). This exposes it in server access logs, browser history, and proxy logs.

**Fix:** After the connection is accepted, send the token as the first WebSocket message and authenticate in the consumer's `receive` handler before allowing any other messages. Reject unauthenticated connections after a short timeout.

---

### 2. Optimistic UI Without Rollback
Notification actions (mark read, delete, clear) update the store optimistically and only show a toast on failure — the UI is left in an inconsistent state. Acceptable for notifications, but this pattern should not be reused for destructive or financial actions.

**Fix:** For sensitive actions, either use a pessimistic update (wait for API response) or implement full rollback by saving the previous state before the optimistic update and restoring it on error.

---

### 3. No Rate Limiting on WebSocket Connections
The HTTP API endpoints have throttling configured (anon: 100/hr, user: 1000/hr), but the WebSocket consumer has no equivalent protection. A single user could open many concurrent connections and hold them open.

**Fix:** Track open connections per user in Redis (the channel layer is already there). Reject connections beyond a per-user limit (e.g. 5 concurrent). Add a connection-open rate limit as well.

---

### 4. Single VPS Deployment
The production `docker-compose.yml` colocates Django, Celery, Redis, Postgres, and MinIO on one machine. There is no horizontal scaling story — if the server goes down, everything goes down.

**Fix (when needed):** Move Postgres and Redis to managed services first (lowest effort, highest reliability gain). Celery workers can then be extracted to a separate container/host. Django/Channels can be load-balanced once the session and cache layers are external.

---

### 5. Stripe Webhook Idempotency
If Stripe retries a webhook event (which it will on any non-2xx response), the handler may process it multiple times — potentially double-charging, double-provisioning, or double-cancelling a subscription.

**Fix:** Store processed Stripe event IDs in a `ProcessedWebhookEvent` table. At the start of each webhook handler, check if the event ID has already been processed and return 200 immediately if so. This is especially critical for `invoice.payment_succeeded` and `customer.subscription.deleted`.
