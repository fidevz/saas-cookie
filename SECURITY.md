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
