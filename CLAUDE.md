# CLAUDE.md

This file describes the project structure, stack, conventions, and commands for this SaaS boilerplate. Read this before making any changes.

---

## Project Structure

```
/
├── backend/        Django REST API + Celery + Django Channels
├── frontend/       Next.js 15 app
├── testing/        Playwright E2E tests
├── marketing/      Autonomous marketing system (AI-operated)
└── new-project.sh  Bootstrap script to rename the boilerplate
```

---

## Backend

### Stack
- **Python 3.12** — runtime
- **Django 5.1** — framework
- **Django REST Framework** — API layer
- **SimpleJWT** — JWT authentication (access token as Bearer, refresh token in HttpOnly cookie)
- **django-allauth + dj-rest-auth** — auth flows including Google OAuth
- **Celery + Redis** — async task queue
- **Django Channels + channels-redis** — WebSocket support (real-time notifications)
- **PostgreSQL** — primary database (via `psycopg` v3)
- **Stripe** — billing and subscriptions
- **Resend** — transactional email (custom Django email backend at `utils/email.py`)
- **drf-spectacular** — auto-generated OpenAPI schema
- **Sentry** — error tracking
- **PostHog** — product analytics (optional, commented out by default)
- **uv** — package manager (not pip, not poetry)
- **ruff** — linting and formatting

### Apps
| App | Responsibility |
|-----|---------------|
| `apps.users` | Custom user model (`CustomUser`), profile management |
| `apps.authentication` | Register, login, logout, password reset, Google OAuth views |
| `apps.tenants` | Multi-tenancy via subdomain — `TenantMiddleware` sets `request.tenant` |
| `apps.teams` | Teams within a tenant, membership, roles |
| `apps.subscriptions` | Stripe plans, checkout, webhooks, subscription state |
| `apps.notifications` | Real-time notifications via WebSockets + Celery |
| `apps.core` | Feature flags, health check, shared utilities |

### Key Conventions
- **Custom user model:** `AUTH_USER_MODEL = "users.CustomUser"` — never reference `auth.User` directly
- **Multi-tenancy:** subdomain-based. `request.tenant` is set by `TenantMiddleware` on every request. It is `None` for root domain, admin, and docs paths.
- **Feature flags:** controlled via `settings.FEATURE_FLAGS` and the `FeatureFlags` class in `apps/core/features.py`. Use `FeatureFlags.teams_enabled()` etc. — never read settings directly in views.
- **JWT auth:** access token (5 min) sent as `Authorization: Bearer <token>`. Refresh token (7 days) in HttpOnly cookie `refresh_token`. Tokens are rotated and blacklisted on refresh.
- **Admin URL:** configurable via `ADMIN_URL` env var (default: `tacomate`) — not `/admin/`
- **API prefix:** all endpoints under `/api/v1/`
- **Pagination:** `PageNumberPagination`, page size 20
- **Throttling:** anon 100/hr, user 1000/hr, login 5/min, register 3/min

### Running the Backend

```bash
cd backend

# Install dependencies
uv sync

# Database setup
make db-create       # createdb saas_boilerplate
make migrate         # run migrations
make seed            # load seed data

# Start server (ASGI via uvicorn)
make run             # http://localhost:8000

# Start Celery worker (separate terminal)
make worker

# Other useful commands
make migrations      # makemigrations
make shell           # shell_plus
make test            # pytest
make lint            # ruff check + format check
make fmt             # ruff format + fix
make db-reset        # drop → create → migrate → seed
```

### Environment Variables (backend/.env)
Copy `backend/.env.example` and fill in:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL URL |
| `REDIS_URL` | Redis URL (Celery + Channels) |
| `RESEND_API_KEY` | Transactional email |
| `STRIPE_SECRET_KEY` | Stripe secret |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SENTRY_DSN` | Sentry DSN (optional) |
| `BASE_DOMAIN` | Root domain, e.g. `yourdomain.com` |
| `APP_NAME` | Application display name |
| `ADMIN_URL` | Custom admin path (default: `tacomate`) |
| `FEATURE_TEAMS` | Enable teams feature (bool) |
| `FEATURE_BILLING` | Enable billing feature (bool) |
| `FEATURE_NOTIFICATIONS` | Enable notifications feature (bool) |

### API Documentation
Available at `/api/docs/` (Swagger UI) and `/api/schema/` (raw OpenAPI JSON) when running in development.

---

## Frontend

### Stack
- **Next.js 15** with App Router
- **React 19**
- **TypeScript**
- **Tailwind CSS + shadcn/ui** (Radix UI primitives)
- **next-intl** — i18n (English + Spanish, extendable)
- **Zustand** — global state management
- **Sonner** — toast notifications
- **Lucide React** — icons

### Key Files
| File/Dir | Purpose |
|----------|---------|
| `src/lib/api.ts` | Centralized API client — use this for all backend requests |
| `src/lib/auth.ts` | Auth utilities |
| `src/lib/features.ts` | Feature flag client (mirrors backend flags) |
| `src/lib/stripe.ts` | Stripe client utilities |
| `src/lib/ws.ts` | WebSocket client for real-time notifications |
| `src/stores/` | Zustand stores: auth, feature flags, notifications, tenant |
| `src/hooks/use-auth.ts` | Auth hook |
| `src/hooks/use-subscription.ts` | Subscription state hook |
| `src/middleware.ts` | Next.js middleware (auth protection, locale routing) |
| `src/i18n/routing.ts` | i18n locale routing config |
| `messages/en.json` | English translations |
| `messages/es.json` | Spanish translations |

### Key Conventions
- All API calls go through `src/lib/api.ts` — never use `fetch` directly in components
- State lives in Zustand stores — don't duplicate in local state unless truly ephemeral
- Adding a new translation string: add to both `messages/en.json` and `messages/es.json`
- Feature flags are available client-side via `src/lib/features.ts` and `src/stores/feature-store.ts`

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install     # or pnpm install

# Development server
npm run dev     # http://localhost:3000

# Type checking
npm run type-check

# Lint
npm run lint

# Production build
npm run build
```

### Environment Variables (frontend/.env)
Copy `frontend/.env.example` and fill in:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe public key |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL |

---

## Testing (E2E)

### Stack
- **Playwright** — browser automation
- **pnpm** — package manager for testing

### Test Coverage
```
testing/e2e/
  auth/           register, login, logout, password reset, Google OAuth
  billing/        checkout, cancellation
  dashboard/      dashboard smoke test
  landing/        landing page
  legal/          privacy, terms pages
  notifications/  real-time notification flow
  pricing/        pricing page
  support/        support page
  team/           team management
```

### Running Tests

```bash
cd testing

# Install dependencies
pnpm install

# Run all tests
pnpm exec playwright test

# Run specific suite
pnpm exec playwright test auth/

# Run with UI
pnpm exec playwright test --ui
```

---

## Multi-Tenancy

Tenant resolution is subdomain-based:
- `yourdomain.com` → `request.tenant = None` (root domain)
- `acme.yourdomain.com` → `request.tenant = <Tenant slug="acme">`
- In development: `acme.localhost` works the same way

Paths exempt from tenant resolution: admin, `/api/docs/`, `/api/schema/`, `/health/`

When building tenant-aware views, use `TenantMixin` from `apps/tenants/mixins.py`.

---

## Feature Flags

Three flags control major features — all default to `True`:

| Flag | Env var | Controls |
|------|---------|---------|
| `TEAMS` | `FEATURE_TEAMS` | Team creation, membership, invitations |
| `BILLING` | `FEATURE_BILLING` | Stripe checkout, subscription management |
| `NOTIFICATIONS` | `FEATURE_NOTIFICATIONS` | WebSocket notifications |

**Backend:** use `FeatureFlags.teams_enabled()` from `apps.core.features`
**Frontend:** use the feature store or `src/lib/features.ts`

---

## File Storage (MinIO)

MinIO is an S3-compatible self-hosted storage server included in `docker-compose.yml`.

Toggle with `USE_S3=True` in `backend/.env`. When enabled, Django uses `django-storages` with `S3Boto3Storage` pointing to the MinIO container.

| Env var | Description |
|---------|-------------|
| `USE_S3` | `True` to use MinIO, `False` for local disk |
| `MINIO_ROOT_USER` | Access key (also used as AWS_ACCESS_KEY_ID) |
| `MINIO_ROOT_PASSWORD` | Secret key |
| `MINIO_BUCKET` | Bucket name (default: `media`) |
| `MINIO_ENDPOINT` | Internal URL (`http://minio:9000` in Docker) |
| `MINIO_PUBLIC_URL` | Public URL for serving files |

MinIO Console: `https://storage.yourdomain.com` (port 9001)

## Initial Setup

When asked to do the initial project setup, always read `SETUP.md` first and follow every step in order.

**Trigger phrases:** "set up the project", "do the initial setup", "configure the server", "deploy for the first time"

**Scripts available in `scripts/`:**
| Script | What it does |
|--------|-------------|
| `setup-dns.sh` | Creates all DNS records in Cloudflare via API |
| `setup-coolify.sh` | Configures Coolify project + app via API |
| `setup-github-secrets.sh` | Pushes all secrets to GitHub Actions |
| `verify-setup.sh` | Verifies the full stack after deploy |
| `bump-version.sh` | Bumps version in pyproject.toml + package.json |

**Tools required (verify before starting):**
```bash
which python3 ssh curl gh jq
gh auth status
```

## Releases

When asked to do a release, always read `RELEASE.md` first and follow every step in order.

**Trigger phrases:** "do a patch release", "release minor", "bump to v1.2.0", "create a release"

**Quick reference:**
```bash
# Tests (run before any release)
make test

# Bump version in pyproject.toml + package.json
scripts/bump-version.sh patch   # or minor / major

# Create GitHub release (after committing + tagging)
gh release create vX.Y.Z --title "vX.Y.Z" --notes "..." --latest
```

Version is stored in two files — always keep them in sync:
- `backend/pyproject.toml` → `version = "X.Y.Z"`
- `frontend/package.json` → `"version": "X.Y.Z"`

## Deployment

Full stack runs via Docker Compose on a single VPS with Coolify. See `ops/COOLIFY_SETUP.md`.

Deploy flow: GitHub Release → GitHub Action → Coolify webhook → rebuild → Telegram notification.

## CI/CD

GitHub Actions workflows:
- `.github/workflows/backend.yml` — runs on push: lint (ruff) + tests (pytest)
- `.github/workflows/frontend.yml` — runs on push: lint (eslint) + type check (tsc)
- `.github/workflows/deploy.yml` — runs on GitHub Release: triggers Coolify deploy + Telegram notification

---

## Adding a New App (Backend)

1. `uv run python manage.py startapp <name> apps/<name>`
2. Add to `LOCAL_APPS` in `config/settings/base.py`
3. Create `apps/<name>/urls.py` and register in `config/urls.py` under `/api/v1/`
4. Run `make migrations && make migrate`
5. Add admin registration in `apps/<name>/admin.py`

## Adding a New API Endpoint

Follow the pattern in existing apps:
- `models.py` → `serializers.py` → `views.py` → `urls.py`
- Views use DRF class-based views (`ModelViewSet`, `APIView`, `generics.*`)
- Always apply appropriate permission classes
- Register URL in the app's `urls.py`, include in `config/urls.py`

## Adding a New Page (Frontend)

- Pages live in `src/app/[locale]/` (locale-prefixed routing via next-intl)
- Add translations to `messages/en.json` + `messages/es.json`
- Use existing Radix/shadcn components — don't add new UI libraries
- API calls via `src/lib/api.ts`

---

## Using This as a Template

Run `./new-project.sh` to scaffold a new project from this boilerplate. It renames references from `saas_boilerplate` to your project name.

After running the script:
1. Fill in `backend/.env` from `backend/.env.example`
2. Fill in `frontend/.env` from `frontend/.env.example`
3. Complete `marketing/context/PRODUCT.md` and `marketing/context/AUDIENCE.md`
4. Set real values in `marketing/strategy/BUDGET.md` and `marketing/decisions/THRESHOLDS.md`
5. Run `make db-reset` in `backend/`
6. Run `npm install && npm run dev` in `frontend/`
