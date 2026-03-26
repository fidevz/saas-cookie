# Architecture Decision Records (ADRs)

> A log of significant technical decisions made in this project — what, why, and what alternatives were considered.
> Add a new entry whenever you make a decision that future developers would ask "why did they do it this way?"

---

## Template

```
## ADR-XXX — [Title]
- **Date:** YYYY-MM-DD
- **Status:** Accepted / Deprecated / Superseded by ADR-YYY

### Context
[What is the situation that led to this decision?]

### Decision
[What did we decide?]

### Alternatives considered
[What else was considered and why it was rejected]

### Consequences
[What are the trade-offs and follow-on decisions?]
```

---

## ADR-001 — ASGI over WSGI

- **Date:** [DATE]
- **Status:** Accepted

### Context
The boilerplate includes real-time notifications via WebSockets. WSGI servers (Gunicorn) do not support WebSocket connections natively.

### Decision
Use ASGI (Daphne) as the server and Django Channels for WebSocket handling.

### Alternatives considered
- **Separate WebSocket service (Soketi, Ably):** adds infrastructure complexity and a new billing dependency. Overkill for a boilerplate.
- **Server-Sent Events:** simpler than WebSockets but one-directional only.
- **Long polling:** works anywhere but inefficient and adds backend load.

### Consequences
- Deployment must use an ASGI server — Gunicorn will not work
- All Django views are still synchronous (ORM is sync) — no performance gain on HTTP from ASGI
- Channels requires Redis for channel layers

---

## ADR-002 — Subdomain-based multi-tenancy

- **Date:** [DATE]
- **Status:** Accepted

### Context
The boilerplate supports multiple tenants. Two common patterns exist: path-based (`domain.com/acme/...`) and subdomain-based (`acme.domain.com`).

### Decision
Subdomain-based tenancy via `TenantMiddleware`.

### Alternatives considered
- **Path-based tenancy:** simpler DNS setup, no wildcard cert needed. But pollutes all URLs, harder to support custom domains per tenant, and feels less professional.
- **Database-per-tenant:** maximum isolation but complex migrations and infrastructure overhead.
- **Schema-per-tenant (PostgreSQL):** django-tenants approach. More isolation than row-level but harder to query across tenants and complex schema management.

### Consequences
- Requires wildcard DNS (`*.domain.com`) and SSL certificate
- `request.tenant` must always be checked in tenant-aware views
- Development requires local subdomain setup (e.g. `acme.localhost`)

---

## ADR-003 — JWT in HttpOnly cookie

- **Date:** [DATE]
- **Status:** Accepted

### Context
JWT tokens must be stored somewhere on the client. The two common options are localStorage and HttpOnly cookies.

### Decision
Access token returned in JSON response body (stored in memory by frontend). Refresh token stored in HttpOnly, Secure, SameSite=Lax cookie.

### Alternatives considered
- **Both tokens in localStorage:** simple but vulnerable to XSS — any malicious script can steal tokens.
- **Both tokens in HttpOnly cookie:** prevents JavaScript access entirely, but requires CSRF protection on all state-changing endpoints.

### Consequences
- Access token in memory means it's lost on page refresh — silent refresh via the cookie-based refresh token handles this
- Refresh token in HttpOnly cookie is not accessible to JavaScript — more secure
- CSRF protection must remain enabled (it is, by default)
- Cross-subdomain auth requires careful cookie domain configuration

---

## ADR-004 — Resend for transactional email

- **Date:** [DATE]
- **Status:** Accepted

### Context
The boilerplate needs a transactional email provider for password resets, welcome emails, etc.

### Decision
Resend, via a custom Django email backend at `utils/email.py`.

### Alternatives considered
- **SendGrid:** industry standard but more complex API, higher price at volume, slower DX.
- **Postmark:** excellent deliverability, good DX, but more expensive.
- **AWS SES:** cheapest at volume but complex setup, poor DX, reputation management burden.
- **SMTP (raw):** Django supports it natively but requires managing an SMTP server.

### Consequences
- Custom backend means swapping providers is a one-file change — low lock-in
- Resend's API is simple and well-documented
- Must verify domain in Resend dashboard before production use

---

## ADR-005 — uv for Python dependency management

- **Date:** [DATE]
- **Status:** Accepted

### Context
Python package management has historically been fragmented (pip, pipenv, poetry). A fast, reliable tool is needed.

### Decision
`uv` for dependency management, with `pyproject.toml` as the single source of truth.

### Alternatives considered
- **pip + requirements.txt:** simple but no lock file, slow, no dependency groups.
- **Poetry:** good DX but slow resolver, not fully PEP-compliant, heavy.
- **Pipenv:** largely abandoned by the community.

### Consequences
- Developers must install uv (`pip install uv` or `brew install uv`)
- `uv.lock` is committed to ensure reproducible installs
- All commands use `uv run python ...` instead of `python ...`

---

## ADR-006 — Periodic cleanup for unverified tenant slugs

- **Date:** 2026-03-25
- **Status:** Accepted

### Context
When a user registers and selects a tenant slug, the `Tenant` record (with its unique slug) is created immediately. If the user never verifies their email, the slug is permanently blocked — enabling slug squatting with throwaway email addresses.

### Decision
A Celery beat task (`cleanup_unverified_tenants`) runs every 6 hours and deletes any `Tenant` whose owner has no verified `EmailAddress` after a 48-hour grace period. The owner `User` is also deleted if they have no remaining tenants or memberships. The grace period is configurable via `UNVERIFIED_TENANT_CLEANUP_HOURS` in settings (default: 48).

Run manually with: `uv run python manage.py cleanup_unverified_tenants`

### Alternatives considered
- **Deferred tenant creation (Redis slug reservation):** Don't create the `Tenant` at registration — reserve the slug in Redis for ~4 hours, then create the tenant when the email is verified. Cleaner in theory but touches the critical registration flow, requires handling orphaned `User` records (which still get created), and needs a "create workspace" fallback page for users who verify after their reservation expires. Too much complexity for the marginal benefit.
- **Aligned TTLs:** Make the email verification link expire at the same time as the slug reservation (~4 hours). Simpler, but unverified `User` records still accumulate and block re-registration with the same email.

### Consequences
- Slugs from abandoned registrations are reclaimed within at most 48 hours after the cleanup runs
- During the 48-hour grace period, a squatted slug is still unavailable — `CheckSlugView` suggests alternatives
- Celery beat must be running in production for this to work (it already is for `check_trial_endings`)
- Cascade behavior: deleting a `Tenant` cascades to `TenantMembership` and `Subscription`; `Tenant.owner` uses `on_delete=PROTECT` so the tenant must be deleted before the user
