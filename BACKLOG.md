# Backlog

Flat list of all open work items. Update this as things get done or new items are added.

Labels: 🔴 blocking · 🟠 pre-launch · 🟡 improvement · 🟢 roadmap

---

## Open

### Security & Reliability
- [x] 🔴 **Stripe webhook idempotency** — no event dedup, risk of double-billing/provisioning (`apps/subscriptions/webhooks.py`)
- [x] 🔴 **WebSocket JWT in query string** — token leaks to server logs (`frontend/src/lib/ws.ts` + `notifications/consumers.py`)
- [x] 🔴 **Plan limits not enforced** — `team_members` capability never checked in invite/accept views (`apps/teams/views.py`)
- [x] 🔴 **No WebSocket rate limiting** — unlimited concurrent connections per user (`notifications/consumers.py`)
- [x] 🟠 **No security event logging** — no audit trail for auth failures, role/email changes (various)
- [x] 🟠 **No DB backup strategy** — nothing configured or documented (`ops/DEPLOYMENT.md`)
- [x] 🟠 **CORS allows any subdomain** — by design for multi-tenancy, but tenant registration must be strictly auth-gated (`config/settings/base.py:270`)

### Content & Legal
- [x] 🔴 **Legal pages have placeholder content** — intentional in the boilerplate; after scaffolding a real project with `new-project.sh`, replace `[PLACEHOLDER]`, `[your company]`, etc. before going live (`frontend/src/app/legal/`)

### Testing & CI
- [x] 🟠 **E2E tests not in CI** — intentionally excluded; Playwright suite is for local/manual use only
### Ops & Monitoring
- [x] 🟠 **`curl | bash` in setup script** — review contents before piping to bash (`ops/COOLIFY_SETUP.md:28`)

---

## Roadmap

### Near-term
- [x] 🟢 **Usage enforcement** — `team_members` capability enforced in `InviteMemberView` + `AcceptInviteView`
- [ ] 🟢 **API keys** — `APIKey` model + DRF auth backend + Settings UI for create/revoke
- [ ] 🟢 **Onboarding flow** — `CompletedStep` model + dismissible checklist on dashboard

### Mid-term
- [x] 🟢 **Audit log** — `AuditLog` model + migration + tests in `apps/core`
- [ ] 🟢 **Admin impersonation** — Django admin action → short-lived token → real session (log all events)
- [ ] 🟢 **In-app changelog** — `Announcement` model via Django admin, delivered via existing notifications infra

### Long-term
- [ ] 🟢 **Data export** — Celery task → CSV/JSON → S3 upload → email link (GDPR)
- [ ] 🟢 **SSO / SAML** — `SAMLConfig` per tenant + `django-saml2-auth`

---

## Done

- [x] Stripe webhook signature verification
- [x] JWT token leakage in OAuth callback URL (C6, C7)
- [x] Open redirect on login `callbackUrl` (H5)
- [x] Race condition on last-admin removal (H8)
- [x] Google OAuth missing `state` CSRF validation (H9)
- [x] Cross-tenant notification manipulation via WebSocket (H10)
- [x] Hardcoded insecure `SECRET_KEY` default (C5)
- [x] Redis/Postgres/MinIO exposed without auth in docker-compose (C1–C4)
- [x] Docker network isolation (H4)
- [x] Mailhog in production compose (H1)
- [x] GitHub Actions SHA pinning — `checkout@v6.0.2`, `setup-node@v6.3.0`, `setup-uv@v7.6.0`, `pnpm/action-setup@v5.0.0` (M10)
- [x] Next.js CVE-2025-66478 — upgraded to 15.5.14 (H6)
- [x] Vulnerable transitive deps — `esbuild`, `picomatch` fixed via pnpm overrides (L7)
- [x] Email templates (all flows)
- [x] robots.txt + sitemap.xml
- [x] Open Graph + Twitter card metadata
- [x] Cookie Policy page
- [x] `AUTH_COOKIE_DOMAIN` for cross-subdomain cookies
- [x] Custom DRF JSON exception handler
- [x] Startup validation of required env vars
- [x] Migration integrity check in CI
- [x] CSP conditional by environment (dev vs prod)
- [x] MinIO bucket public-read removed → pre-signed URLs
- [x] JSON-LD structured data on landing page
- [x] Web app manifest
- [x] pnpm audit fails CI on high severity
- [x] Stripe webhook idempotency — `StripeWebhookEvent` model + dedup in `WebhookView` + cleanup task
- [x] Celery result expiry configured
- [x] Docker resource limits
- [x] Test coverage threshold (70%)
- [x] Canonical URL + hreflang metadata
- [x] 404 + error pages for protected routes
- [x] Email verification countdown localStorage → Zustand
- [x] ARIA labels audit on all form inputs
- [x] Notifications full page (infinite scroll, delete, clear read)
