# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to report

Email: **[SECURITY EMAIL]**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

### What to expect

| Timeline | Action |
|----------|--------|
| 24 hours | Acknowledgement of your report |
| 72 hours | Initial assessment and severity classification |
| 7 days | Status update with estimated resolution timeline |
| 30 days | Target resolution for critical and high severity issues |

We will keep you informed throughout the process.

### Disclosure policy

We follow coordinated disclosure. Please:
- Give us reasonable time to fix the issue before public disclosure
- Do not access or modify user data during testing
- Do not perform DoS attacks
- Test only against your own account or our designated test environment

We do not currently offer a bug bounty program, but we are grateful for responsible disclosures and will publicly credit you (with your permission).

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest | Yes |
| Previous minor | Security fixes only |
| Older | No |

---

## Security Measures

This boilerplate implements the following by default:

### Authentication
- JWT with short-lived access tokens (5 minutes)
- Refresh tokens stored in HttpOnly, Secure, SameSite=Lax cookies
- Token rotation and blacklisting on refresh
- Rate limiting on login (5/min) and registration (3/min) endpoints

### Transport
- HTTPS enforced in production (`AUTH_COOKIE_SECURE=True`)
- CORS restricted to configured origins only
- HSTS enabled via Django's `SecurityMiddleware`

### Application
- CSRF protection enabled
- SQL injection protection via Django ORM (never raw queries with user input)
- XSS protection via Django template escaping + React's default escaping
- Clickjacking protection (`X-Frame-Options`)
- Content Security Policy: [configure per your needs]
- Admin URL obscured via `ADMIN_URL` environment variable
- Debug mode disabled in production

### Data
- Passwords hashed with Argon2 / PBKDF2
- Payment data never stored — processed exclusively by Stripe
- Database encrypted at rest (provider-level)
- Data in transit encrypted via TLS 1.2+

### Dependencies
- `pip-audit` runs in CI to detect known vulnerabilities in dependencies
- Dependencies pinned and reviewed on update

---

## Known Security Considerations

When extending this boilerplate, pay attention to:

1. **Tenant isolation** — always filter querysets by `request.tenant`. Use `TenantMixin` from `apps/tenants/mixins.py`. Never return cross-tenant data.

2. **File uploads** — validate file type and size. Never serve uploaded files from the same domain as the app (use S3/R2). Never execute uploaded files.

3. **Webhook verification** — always verify Stripe webhook signatures using `STRIPE_WEBHOOK_SECRET`. The boilerplate does this in `apps/subscriptions/webhooks.py`.

4. **Environment variables** — never commit `.env` files. Never log secrets. Rotate keys if they are ever exposed.

5. **Celery tasks** — tasks run with full app context. Validate inputs before processing. Don't pass unsanitized user input directly to tasks.

6. **WebSockets** — authenticate WebSocket connections. The boilerplate uses JWT validation in consumers. Never trust the WebSocket connection without verifying the user.

---

## Internal Audit — 2026-03-25

Full-stack security audit findings. Work through these in priority order before first production deploy.

### Critical

| ID | File | Line | Description | Status |
|----|------|------|-------------|--------|
| C1 | `docker-compose.yml` | 123 | Redis has no password — unauthenticated access to session tokens, Celery queues, and cache | **Fixed** |
| C2 | `docker-compose.yml` | 100 | PostgreSQL port `5432` bound to `0.0.0.0` — direct DB access if firewall is misconfigured | **Fixed** |
| C3 | `docker-compose.yml` | 142 | MinIO ports 9000/9001 exposed — S3 API and admin console reachable without proxy | **Fixed** |
| C4 | `apps/subscriptions/views.py` | 228 | Stripe webhook skips signature verification when `STRIPE_WEBHOOK_SECRET` is unset | **Fixed** |
| C5 | `config/settings/base.py` | 17 | Hardcoded insecure `SECRET_KEY` default — token forgery if env var not set in production | **Fixed** |
| C6 | `frontend/src/app/auth/callback/page.tsx` | 43 | Bearer token passed in URL query param (`?access=`) — leaks to browser history, proxy logs, referrer headers | **Fixed** |
| C7 | `frontend/src/components/auth/register-form.tsx` | 141 | Access token embedded in redirect URL during invite registration — same leakage risk as C6 | **Fixed** |

### High

| ID | File | Line | Description | Status |
|----|------|------|-------------|--------|
| H1 | `docker-compose.yml` | 183 | Mailhog (dev email catcher) included in production compose — leaks password reset tokens and verification links | **Fixed** |
| H2 | `.env.example` | 4, 13 | Default passwords set to `changeme` — may be deployed as-is | **Fixed** |
| H3 | `ops/COOLIFY_SETUP.md` | 28 | `curl \| bash` install pattern — arbitrary code execution if DNS or CDN is compromised | Open — verify script before piping |
| H4 | `docker-compose.yml` | all | No Docker network isolation — compromised frontend container can reach PostgreSQL and Redis directly | **Fixed** |
| H5 | `frontend/src/components/auth/login-form.tsx` | 67 | Open redirect — `callbackUrl` query param used in redirect without validation | **Fixed** |
| H6 | `frontend/package.json` | — | CVE-2025-66478 — Next.js 15.0.4 has a known security vulnerability | **Fixed** — upgraded to 15.5.14 |
| H7 | `apps/users/views.py` | 50 | Email change flow does not verify ownership of the new address before confirming the change | **Not a bug** — flow already sends confirmation to new address |
| H8 | `apps/teams/views.py` | 207 | Race condition on last-admin check — non-atomic query allows concurrent removal of all admins | **Fixed** |
| H9 | `apps/authentication/views.py` | 467 | Google OAuth callback does not validate the `state` parameter — CSRF on the OAuth flow | **Fixed** |
| H10 | `apps/notifications/consumers.py` | 126 | `_mark_read()` does not filter by tenant — cross-tenant notification manipulation via WebSocket | **Fixed** |
| H11 | `.github/workflows/deploy.yml` | 19 | Secrets potentially visible in curl verbose output — no `--silent` flag | **Fixed** |
| H12 | `apps/teams/models.py` | 29 | Invitation tokens use `uuid.uuid4()` instead of `secrets.token_urlsafe(32)` | **Not a bug** — UUID4 uses `os.urandom(16)` (128-bit CSPRNG) |

### Medium

| ID | File | Line | Description | Status |
|----|------|------|-------------|--------|
| M1 | `config/settings/base.py` | 270 | CORS uses a broad subdomain regex — any subdomain of `BASE_DOMAIN` is whitelisted | Open — required for multi-tenant; ensure subdomain registration is auth-gated |
| M2 | `.github/workflows/*.yml` | — | No `permissions:` block — workflows inherit default write permissions for `GITHUB_TOKEN` | **Fixed** |
| M3 | `apps/authentication/views.py` | 548 | Password reset shares throttle with login — no dedicated per-email rate limit | **Fixed** |
| M4 | `apps/authentication/views.py` | 252 | No rate limit on email verification endpoint — brute force possible | **Fixed** |
| M5 | `frontend/src/components/auth/email-verification-gate.tsx` | 10 | Email resend cooldown enforced only in localStorage — trivially bypassed | **Not a bug** — server-side `ResendVerificationThrottle` (12/hour) is the real guard |
| M6 | `frontend/src/lib/api.ts` | 84 | CSRF token is optional — state-changing requests proceed without header if cookie is absent | **Not a bug** — JWT Bearer auth already prevents CSRF on API endpoints; CSRF token is defense-in-depth |
| M7 | `frontend/src/app/error.tsx` | 18 | `console.error(error)` in production — stack traces leak in browser console | **Fixed** |
| M8 | `apps/subscriptions/views.py` | 116 | Raw Stripe error messages returned to client — internal API structure disclosed | **Fixed** |
| M9 | `apps/teams/views.py` | 77 | `GetInvitationView` is `AllowAny` and returns invited email + tenant name — enables email enumeration | **Fixed** |
| M10 | `.github/workflows/*.yml` | — | GitHub Actions pinned to `@v4` tags, not commit SHAs — supply chain risk if tag is reassigned | **Fixed** — pinned to latest release SHAs (checkout@v6.0.2, setup-node@v6.3.0, setup-uv@v7.6.0, pnpm/action-setup@v5.0.0) |
| M11 | `frontend/next.config.ts` | 38 | Dev CSP uses `unsafe-eval` + `unsafe-inline` — risk if accidentally shipped to production | **Not a bug** — production CSP already strict; dev CSP is intentional |
| M12 | `frontend/src/app/auth/check-email/page.tsx` | 15 | Email from query param rendered in translation string without format validation | **Fixed** |

### Low

| ID | File | Line | Description | Status |
|----|------|------|-------------|--------|
| L1 | `apps/authentication/views.py` | 539 | OAuth callback redirects with `?access=` token — visible in browser history and logs | **Fixed** (same as C6) |
| L2 | `frontend/src/lib/ws.ts` | 1 | WebSocket defaults to `ws://` (unencrypted) — should enforce `wss://` in production | **Fixed** |
| L3 | Backend + Frontend | — | No Content-Security-Policy headers configured | **Not a bug** — CSP already in `next.config.ts` |
| L4 | Various | — | Insufficient security event logging — no audit trail for role changes, email changes, auth failures | Open |
| L5 | `ops/DEPLOYMENT.md` | — | No database backup strategy documented in pre-deploy checklist | Open |
| L7 | `frontend/pnpm-lock.yaml` | — | Deprecated `glob` transitive dependency — run `pnpm audit fix` | **Fixed** — updated `eslint-config-next` to 15.5.14, added pnpm overrides for `esbuild >=0.25.0` and `picomatch ^2.3.2/^4.0.4` |
