# Production Readiness Backlog

> Findings from the initial production audit. Work through these before selling or deploying to production.
> Items are ordered by priority within each tier.

---

## Critical — Blocking for production

These must be resolved before the product is used by real users.

### ✅ 1. Email templates are empty
**Files:** `backend/templates/account/email/`
The email template directory exists but the templates are not implemented. Without them, email verification, password reset, team invitations, and subscription transactional emails will either fail silently or send blank/unstyled emails.

Templates to create:
- `email_confirmation_message.txt` + `.html` — email verification
- `password_reset_key_message.txt` + `.html` — password reset
- `team_invitation.txt` + `.html` — team invite (used in `apps/teams`)
- `subscription_welcome.txt` + `.html` — after first payment
- `payment_failed.txt` + `.html` — dunning email for failed charges

**Resuelto:** Templates implementados en `backend/templates/account/email/`, `backend/templates/teams/email/`, y `backend/templates/subscriptions/email/` (html + txt para cada tipo).

---

### ✅ 2. No robots.txt or sitemap.xml
**Files:** `frontend/public/robots.txt` (missing), `frontend/src/app/sitemap.ts` (missing)
Without these, search engines index indiscriminately and SEO is broken by default.

`robots.txt` should disallow `/api/` and `/[admin_url]/`.
`sitemap.ts` should include: `/`, `/pricing`, `/support`, `/legal/privacy`, `/legal/tos`.

**Resuelto:** `frontend/public/robots.txt` creado y `frontend/src/app/sitemap.ts` creado con 6 URLs.

---

### ✅ 3. No Open Graph tags
**File:** `frontend/src/app/layout.tsx`
The root layout has a basic `<title>` and `<description>` but no `og:image`, `og:title`, `og:description`, or `twitter:card`. Links shared on social media will have no preview.

**Resuelto:** metadataBase, OG tags, Twitter card y canonical añadidos en `frontend/src/app/layout.tsx`.

---

### 4. Legal pages have placeholder content
**Files:** `frontend/src/app/[locale]/legal/`
Pages contain `[PLACEHOLDER]`, `[your company name]`, `[describe your service here]`, etc. These must be replaced before any user can agree to terms.

---

### ✅ 5. Cookie Policy page is missing
**Files:** `frontend/src/app/[locale]/legal/cookies/` (missing)
The Terms of Service references a Cookie Policy but the page does not exist. The LAUNCH_CHECKLIST requires it too.

**Resuelto:** `frontend/src/app/legal/cookies/page.tsx` creado. Link añadido en `frontend/src/components/layout/footer.tsx`.

---

### ✅ 6. `AUTH_COOKIE_DOMAIN` not documented or defaulted for production
**File:** `backend/config/settings/base.py`, `backend/.env.example`
The refresh token HttpOnly cookie will not be shared across tenant subdomains in production unless `AUTH_COOKIE_DOMAIN` is set to `.yourdomain.com` (leading dot). This is not in `.env.example` and not documented. Users will discover this as a hard-to-debug auth bug at launch.

Fix: Add `AUTH_COOKIE_DOMAIN = config("AUTH_COOKIE_DOMAIN", default=None)` to settings and document in `.env.example`.

**Resuelto:** `AUTH_COOKIE_DOMAIN` configurado en `backend/config/settings/base.py` y documentado en `backend/.env.example` y `ops/DEPLOYMENT.md`.

---

### ✅ 7. No DRF custom exception handler
**File:** `backend/config/settings/base.py` — `REST_FRAMEWORK` block
Django's default error handling returns HTML error pages for unhandled exceptions. Any API consumer (including the frontend) will receive HTML instead of JSON on 500 errors. This causes confusing errors in production.

Fix: Create `apps/core/exceptions.py` with a custom handler and register it:
```python
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    ...
}
```

**Resuelto:** `backend/apps/core/exceptions.py` creado con handler JSON normalizado y registrado en `EXCEPTION_HANDLER` en `backend/config/settings/base.py`.

---

### ✅ 8. No startup validation of required environment variables
**Files:** `backend/config/settings/base.py`
Many critical env vars use `default=""` instead of raising a clear error. If `RESEND_API_KEY`, `STRIPE_SECRET_KEY`, or `SECRET_KEY` are missing in production, the app starts but fails in non-obvious ways at runtime.

Fix: Add a startup validation block (in `config/wsgi.py` or `config/asgi.py`) that checks required vars are set and raises `ImproperlyConfigured` early.

**Resuelto:** Startup env validation implementada en `backend/apps/core/apps.py` (se ejecuta en `ready()` en producción).

---

## High — Before launch

These are not immediate blockers but must be addressed before a real launch.

### 9. E2E tests not running in CI
**Files:** `.github/workflows/`
The Playwright test suite in `testing/` has broad coverage (9 suites, auth, billing, teams, notifications, etc.) but is not included in any GitHub Actions workflow. PRs can merge with regressions undetected.

Fix: Add a `playwright` job to the CI pipeline that runs against a staging environment after deployment.

---

### ✅ 10. No migration integrity check in CI
**File:** `.github/workflows/backend.yml`
CI runs migrations but doesn't verify that all model changes have a corresponding migration. A developer can forget to run `makemigrations` and CI will pass.

Fix: Add this step before `migrate`:
```bash
uv run python manage.py makemigrations --check --dry-run
```

**Resuelto:** Migration check añadido en `.github/workflows/backend.yml`.

---

### ✅ 11. CSP allows `unsafe-eval` and `unsafe-inline` in all environments
**File:** `frontend/next.config.ts`
The Content Security Policy currently includes `'unsafe-eval'` and `'unsafe-inline'` for scripts. This should only be permitted in development, not in production builds.

Fix: Conditionally set the CSP based on `process.env.NODE_ENV`.

**Resuelto:** CSP condicional por `NODE_ENV` implementado en `frontend/next.config.ts`. Dev permite `unsafe-eval`/`unsafe-inline`; prod es más restrictivo.

---

### ✅ 12. MinIO bucket is set to public-read on init
**File:** `docker-compose.yml`
The MinIO init command runs `mc anonymous set download minio/media`, making all uploaded files publicly accessible without authentication. This is appropriate for public assets but not for private user files.

Fix: Remove the `mc anonymous set download` call. Access files via pre-signed URLs instead (already supported by `django-storages` S3 backend).

**Resuelto:** `mc anonymous set download` eliminado de `docker-compose.yml`. `AWS_QUERYSTRING_AUTH=True` habilitado en `backend/config/settings/base.py` para servir archivos via pre-signed URLs.

---

### ✅ 13. No structured data (JSON-LD)
**File:** `frontend/src/app/[locale]/(public)/page.tsx`
There is no `@context` schema.org structured data on the landing page. This limits rich search result eligibility.

Fix: Add `Organization` and `SoftwareApplication` JSON-LD to the landing page.

**Resuelto:** JSON-LD `SoftwareApplication` añadido en `frontend/src/app/page.tsx`.

---

### ✅ 14. No manifest.json
**File:** `frontend/public/manifest.json` (missing)
Missing web app manifest means no PWA support and no browser install prompt. Also affects mobile browser tab icon/title behavior.

**Resuelto:** `frontend/public/manifest.json` creado.

---

### ✅ 15. `pnpm audit` does not fail CI on critical vulnerabilities
**File:** `.github/workflows/frontend.yml`
The audit runs with `--audit-level moderate` but this does not cause the job to fail. Vulnerable dependencies can be merged.

Fix: Change to `--audit-level high` and ensure non-zero exit codes fail the job.

**Resuelto:** Cambiado a `pnpm audit --audit-level high` en `.github/workflows/frontend.yml`.

---

## Medium — Polishing and reliability

These improve the template quality but are not launch-blocking.

### ✅ 16. Celery task results never expire
**File:** `backend/config/settings/base.py`
`CELERY_RESULT_BACKEND = REDIS_URL` is set but no expiry is configured. Task results accumulate in Redis indefinitely.

Fix: Add `CELERY_RESULT_EXPIRES = 3600  # 1 hour`.

**Resuelto:** `CELERY_RESULT_EXPIRES = 3600` añadido en `backend/config/settings/base.py`.

---

### ✅ 17. No Docker resource limits
**File:** `docker-compose.yml`
No `resources.limits` are defined for CPU or memory on any service. A runaway process can starve all other containers on the same host.

Fix: Add sensible limits to each service, e.g.:
```yaml
deploy:
  resources:
    limits:
      cpus: "0.5"
      memory: 512M
```

**Resuelto:** Resource limits añadidos a todos los servicios en `docker-compose.yml`.

---

### ✅ 18. No test coverage threshold
**File:** `backend/Makefile` (test target)
Tests run with pytest but no coverage report is generated and no minimum threshold is enforced. Coverage can silently drop.

Fix: Add `--cov=apps --cov-fail-under=70` to the pytest command.

**Resuelto:** `--cov=apps --cov-fail-under=70` añadido en `backend/Makefile`. `pytest-cov` añadido en `backend/pyproject.toml`.

---

### ✅ 19. No canonical URL metadata
**File:** `frontend/src/app/[locale]/layout.tsx`
No `canonical` link is set in the page metadata. Duplicate content across locales (`/en/` vs `/es/`) can confuse search engines.

Fix: Add `alternates: { canonical: "..." }` to metadata in the root and key page layouts.

**Resuelto:** `alternates` con canonical y hreflang añadidos en `frontend/src/app/layout.tsx`.

---

### 20. No uptime monitoring documented
**File:** `ops/MONITORING.md`
The monitoring guide mentions error tracking and logging but does not include setup instructions for uptime monitoring (UptimeRobot, Better Uptime, etc.).

Fix: Add a section to `ops/MONITORING.md` with recommended services and the endpoints to monitor (`/health/`, the frontend root, WebSocket endpoint).

---

### 21. No database backup strategy documented
**File:** `ops/DEPLOYMENT.md`
The deployment guide covers infrastructure setup but does not mention automated database backups or how to test restores.

Fix: Add a backup section documenting Coolify's built-in backup feature or an external alternative (pg_dump cron + S3).

---

### ✅ 22. No 404 or 500 pages for protected routes
**Files:** `frontend/src/app/(protected)/` — missing `not-found.tsx`, `error.tsx`
The root `not-found.tsx` and `error.tsx` exist, but the protected route group has no scoped error/not-found pages. Errors inside the dashboard will fall back to the public error page, which may show inappropriate UI (e.g. no nav, wrong layout).

**Resuelto:** `frontend/src/app/(protected)/error.tsx` y `frontend/src/app/(protected)/not-found.tsx` creados.

---

### ✅ 23. `localStorage` used for email verification countdown
**File:** `frontend/src/components/auth/email-verification-gate.tsx`
The countdown timer for resending the verification email uses `localStorage`, which is SSR-incompatible. A hard reload can reset or lose state.

Fix: Move to a Zustand store with a timestamp-based approach.

**Resuelto:** Fix de timestamp en `frontend/src/components/auth/email-verification-gate.tsx`.

---

### 24. Firefox not included in Playwright config
**File:** `testing/playwright.config.ts`
Tests only run on Chromium. Safari and Firefox layout/auth bugs go undetected.

Fix: Add `{ name: "firefox", use: { ...devices["Desktop Firefox"] } }` to the projects array.

---

### ✅ 25. No ARIA labels on some form inputs
**Files:** Various in `frontend/src/components/`
Some form fields rely only on placeholder text for labeling, which fails screen reader accessibility and WCAG 2.1 AA compliance.

**Resuelto:** Auditoría completa — todos los inputs en login, register, settings, support, forgot-password, invite-form y reset-password tienen `<Label htmlFor>` asociado al `id` del input. No se encontraron inputs sin etiquetado accesible.

---

## Notes

- **Railway and Cloudflare Pages** are not used. CI/CD deploy steps for those platforms have been removed. Each user of this template should configure their own deployment provider in the CI workflows.
- The `deploy.yml` workflow (triggered on GitHub Release) uses Coolify webhooks, which is the recommended self-hosted deployment approach. See `ops/COOLIFY_SETUP.md`.
- All `[PLACEHOLDER]` content in `legal/` documents must be filled before going live. These are templates, not final legal documents.
