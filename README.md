# SaaS Boilerplate

A production-ready SaaS starter kit with everything you need to go from zero to launch — backend, frontend, billing, auth, multi-tenancy, marketing, and ops.

## What's Included

### Product
| Layer | Stack |
|-------|-------|
| **Backend API** | Django 5.1 + DRF + Celery + Django Channels |
| **Frontend** | Next.js 15 + React 19 + Tailwind + shadcn/ui |
| **Auth** | JWT + Google OAuth (django-allauth) |
| **Billing** | Stripe (subscriptions, webhooks, portal) |
| **Real-time** | WebSockets via Django Channels + Redis |
| **Email** | Resend |
| **Multi-tenancy** | Subdomain-based (acme.yourdomain.com) |
| **i18n** | English + Spanish (next-intl) |
| **Feature flags** | Env-based, synced frontend ↔ backend |
| **Testing** | pytest (unit) + Playwright (E2E) |
| **Error tracking** | Sentry |
| **Analytics** | PostHog |
| **CI/CD** | GitHub Actions |

### Business
| Area | What's included |
|------|----------------|
| **Marketing** | Autonomous AI marketing system (Publer, Meta Ads, Google Ads, TikTok, Reddit, Pinterest) |
| **Growth** | Onboarding playbook, retention, PLG, referral program, NPS |
| **Legal** | Privacy Policy, Terms of Service, Cookie Policy templates |
| **Ops** | Deployment guide, incident response, monitoring, launch checklist |
| **Support** | Customer success playbook, FAQ, cancellation flows |

---

## Quick Start

### Prerequisites
- Python 3.12+, [uv](https://github.com/astral-sh/uv)
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 1. Use this template

```bash
git clone <repo-url> my-saas
cd my-saas
./new-project.sh   # renames the boilerplate to your project
```

### 2. Backend

```bash
cd backend
cp .env.example .env   # fill in your values
uv sync
make db-reset          # create db + migrate + seed
make run               # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local   # fill in your values
pnpm install
pnpm dev                     # http://localhost:3000
```

### 4. E2E Tests

```bash
cd testing
cp .env.example .env
pnpm install
pnpm exec playwright test
```

---

## Seed Data

After `make db-reset` in `backend/`, the following test data is created:

| Resource | Value |
|----------|-------|
| Admin user | `admin@test.com` / `testpassword123` |
| Test tenant | `test-company` → `test-company.localhost` |
| Plans | Starter ($9/mo), Pro ($29/mo, 14-day trial) |
| Admin panel | http://localhost:8000/tacomate/ |
| API docs | http://localhost:8000/api/docs/ |

---

## Project Structure

```
/
├── backend/          Django REST API
├── frontend/         Next.js app
├── testing/          Playwright E2E tests
├── marketing/        Autonomous marketing system
├── growth/           Onboarding, retention, PLG, NPS
├── legal/            Privacy, Terms, Cookie policy templates
├── ops/              Deployment, incident response, monitoring
├── support/          FAQ, customer success
├── docs/             Architecture, decision records
├── CLAUDE.md         AI assistant context for this repo
├── SECURITY.md       Security policy and vulnerability reporting
└── new-project.sh    Bootstrap script
```

---

## Key Features

### Multi-tenancy
Subdomain-based. Each tenant gets their own `slug.yourdomain.com`. The `TenantMiddleware` resolves the tenant on every request. Works on `slug.localhost` in development.

### Auth
JWT access token (5 min, in-memory) + refresh token (7 days, HttpOnly cookie). Google OAuth via django-allauth. Silent token refresh on expiry.

### Billing
Full Stripe integration: plans, checkout, customer portal, webhook handling, trial periods. Subscription state driven entirely by Stripe webhooks.

### Feature Flags
Three built-in flags (`FEATURE_TEAMS`, `FEATURE_BILLING`, `FEATURE_NOTIFICATIONS`) controlled via env vars. Synced to the frontend automatically. Add your own in `config/settings/base.py`.

### Autonomous Marketing
The `marketing/` folder contains a complete AI-operated marketing system. Fill in `marketing/context/PRODUCT.md`, set budgets in `marketing/strategy/BUDGET.md`, configure your API keys, and Claude runs campaigns on a cron schedule.

---

## Customizing for Your Project

1. Run `./new-project.sh` to rename from `saas_boilerplate` to your project name
2. Fill in `marketing/context/PRODUCT.md` — your product details
3. Fill in `marketing/context/AUDIENCE.md` — your ICPs
4. Set real numbers in `marketing/strategy/BUDGET.md` and `marketing/decisions/THRESHOLDS.md`
5. Replace placeholder content in `legal/` documents and publish them
6. Complete `ops/LAUNCH_CHECKLIST.md` before going live
7. Work through `docs/TODO.md` — known production readiness gaps to address
8. Read `CLAUDE.md` for full developer context

---

## Documentation

| Document | Description |
|----------|-------------|
| [`CLAUDE.md`](./CLAUDE.md) | Full stack, conventions, and commands for AI assistance |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | System design and request flows |
| [`docs/DECISIONS.md`](./docs/DECISIONS.md) | Why key technical choices were made |
| [`docs/TODO.md`](./docs/TODO.md) | Known production gaps and backlog |
| [`ops/KAMAL_SETUP.md`](./ops/KAMAL_SETUP.md) | Step-by-step production deployment (Kamal 2 on Hetzner) |
| [`ops/DEPLOYMENT.md`](./ops/DEPLOYMENT.md) | Deployment reference, env vars, rollback |
| [`ops/LAUNCH_CHECKLIST.md`](./ops/LAUNCH_CHECKLIST.md) | Pre-launch checklist |
| [`SECURITY.md`](./SECURITY.md) | Security policy and reporting |

---

## License

[MIT](./LICENSE)
