# Setup Playbook

> Claude reads this file to execute the full setup of a new project.
> To trigger: tell Claude "do the initial setup", "set up the project", or "deploy for the first time".

---

## Overview

Setup has three phases:

| Phase | Time | What happens |
|-------|------|--------------|
| **A — Bootstrap** | 5 min | Run `new-project.sh`, rename everything |
| **B — Local dev** | 10 min | Get backend + frontend running on your machine |
| **C — Production** | 30–60 min | Deploy to Coolify on Hetzner |

You can stop after Phase B and come back to Phase C when you're ready to go live.

---

## Prerequisites

Install these before starting:

```bash
# Python + backend
brew install python@3.12
pip install uv

# Node + frontend
brew install node@20 pnpm

# Database + cache
brew install postgresql@15 redis

# Tools
brew install gh jq
gh auth login   # authenticate with GitHub
```

Verify:
```bash
python3 --version    # 3.12+
uv --version
node --version       # 20+
pnpm --version
psql --version       # 15+
redis-cli ping       # PONG
gh auth status
```

---

## Phase A — Bootstrap

### A1. Clone the boilerplate

```bash
git clone <repo-url> saas-boilerplate
cd saas-boilerplate
```

### A2. Run the initializer

```bash
./new-project.sh
```

The script will prompt for:
- **Project name** (snake_case, e.g. `my_saas`) — used as Python package name and DB name
- **Display name** (e.g. `My SaaS`) — used in UI and emails
- **Production domain** (e.g. `myapp.com`) — used in env files and docs
- **Admin URL slug** (e.g. `my-secret-admin`) — the path for the Django admin panel
- **Output directory** — where the new project is created (default: `../my_saas`)
- Feature toggles: teams, billing, notifications

The script:
1. Copies `backend/`, `frontend/`, `testing/`, `.github/`, `docs/`, `ops/`
2. Copies `docker-compose.yml`, `README.md`, `CLAUDE.md`, `SETUP.md`, `RELEASE.md`
3. Renames all `saas_boilerplate` → your project name across all files
4. Substitutes `{{DOMAIN}}` → your domain in `.env.example` and docs
5. Generates a random `SECRET_KEY`
6. Creates `backend/.env` (dev-ready) and `frontend/.env.local`
7. Initializes a fresh git repo with an initial commit

After it finishes, switch to your new project:

```bash
cd ../my_saas   # or wherever you pointed the output
```

---

## Phase B — Local Development

### B1. Backend

```bash
cd backend

# Install Python dependencies
uv sync

# Create the database and load seed data
make db-reset   # createdb → migrate → seed

# Start the API server (http://localhost:8000)
make run
```

**Seed data created by `make db-reset`:**

| Resource | Value |
|----------|-------|
| Admin user | `admin@test.com` / `testpassword123` |
| Test tenant | `test-company` → `test-company.localhost` |
| Plans | Starter ($9/mo), Pro ($29/mo, 14-day trial) |
| Admin panel | `http://localhost:8000/<your-admin-url>/` |
| API docs | `http://localhost:8000/api/docs/` |

### B2. Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
pnpm install

# Start the dev server (http://localhost:3000)
pnpm dev
```

### B3. Tenant subdomain (local)

To test tenant subdomains locally, add an entry to `/etc/hosts`:

```bash
sudo sh -c 'echo "127.0.0.1 test-company.localhost" >> /etc/hosts'
```

Then visit `http://test-company.localhost:3000`. The frontend middleware routes `*.localhost` to the correct tenant automatically. The backend resolves tenant subdomains when `BASE_DOMAIN=localhost` (hardcoded in `development.py`).

For each new tenant you create during local dev, add a corresponding line to `/etc/hosts`.

### B4. Fill in API keys (optional for basic dev)

Open `backend/.env`. Most fields are pre-filled. The ones you need to fill in depend on which features you're testing:

| Key | Needed for | Where to get it |
|-----|------------|-----------------|
| `STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY` | Billing flow | Stripe Dashboard → API keys (use test keys `sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhooks locally | `stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook/` |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | Google OAuth | GCP Console → OAuth 2.0 credentials |
| `RESEND_API_KEY` | Sending real emails | resend.com |
| `SENTRY_DSN` | Error tracking | sentry.io (optional) |

**Skipping services locally:**
- **Email:** dev settings use Mailhog (SMTP on port 1025). Install with `brew install mailhog` and run `mailhog` — UI at `http://localhost:8025`. Or change `EMAIL_BACKEND` in `development.py` to `django.core.mail.backends.console.EmailBackend` to print emails to the terminal instead.
- **Billing:** set `FEATURE_BILLING=false` in `.env` to disable the billing flow entirely.
- **Notifications:** dev settings use an in-memory channel layer — WebSockets work without Redis.
- **Celery:** dev settings run tasks synchronously (`CELERY_TASK_ALWAYS_EAGER=True`) — no worker needed.

### B5. Run tests

```bash
# Backend
cd backend && make test

# Frontend type check + lint
cd frontend && pnpm type-check && pnpm lint

# E2E (requires both servers running)
cd testing && pnpm install && pnpm exec playwright test
```

---

## Phase C — Production (Coolify on Hetzner)

> For the full Coolify setup walkthrough, see `ops/COOLIFY_SETUP.md`.
> This section summarises the steps Claude can execute autonomously.

### C1. Human-only prerequisites

These require browser flows, credit cards, or accounts Claude cannot create:

#### First project ever (~50 min, one-time)
| Task | Where |
|------|-------|
| Create Hetzner account + VPS (CX22 to start) | hetzner.com |
| Add domain to Cloudflare | cloudflare.com |
| Create Stripe account | dashboard.stripe.com |
| Create Resend account + verify domain | resend.com |
| Create Sentry org | sentry.io |
| Create Telegram bot | @BotFather on Telegram |

#### Subsequent projects (~15 min)
| Task | Where |
|------|-------|
| Provision new VPS on Hetzner (or reuse existing) | hetzner.com |
| Add new domain to Cloudflare | cloudflare.com |
| Create Stripe Products + Prices for this project | dashboard.stripe.com |
| Verify new domain in Resend | resend.com |
| Create new Sentry project in existing org | sentry.io |
| Create new GCP OAuth project | console.cloud.google.com |

Most services are reusable across projects — no new account needed:

| Service | Reuse account? | Per-project action |
|---------|---------------|--------------------|
| Stripe | ✅ | New Products + Prices + webhook |
| Cloudflare | ✅ | New zone (domain) |
| Sentry | ✅ | New project → new DSN |
| Resend | ✅ | Verify new domain |
| Google OAuth | ✅ | New GCP project |
| Hetzner | ✅ | New VPS (or share via Coolify) |
| Telegram | ✅ | Same bot, new chat ID |

### C2. Gather credentials

Before asking Claude to deploy, have these ready:

```
SERVER_IP=            # Hetzner VPS public IP
SSH_KEY_PATH=         # e.g. ~/.ssh/id_ed25519
DOMAIN=               # e.g. myapp.com
CLOUDFLARE_TOKEN=     # API token with Zone:Edit + DNS:Edit
CLOUDFLARE_ZONE_ID=   # Cloudflare zone ID for the domain
GITHUB_REPO=          # e.g. username/my-saas
ADMIN_EMAIL=          # superuser email
ADMIN_PASSWORD=       # initial password (change after first login)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=   # e.g. hello@myapp.com
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SENTRY_DSN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
# STRIPE_WEBHOOK_SECRET — get this after Step C7
```

Secrets Claude generates automatically:
- `SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `ADMIN_URL`

### C3. Configure DNS

```bash
scripts/setup-dns.sh
```

Creates in Cloudflare:
- `A @ → SERVER_IP` (root domain → frontend)
- `A api → SERVER_IP` (backend)
- `A storage → SERVER_IP` (MinIO console)
- `A * → SERVER_IP` (wildcard → tenant subdomains)

### C4. Install Coolify on the VPS

```bash
ssh -i $SSH_KEY_PATH root@$SERVER_IP \
  "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash"
```

Takes ~3 min. Verify: `curl -f http://$SERVER_IP:8000/api/v1/health`

### C5. Configure Coolify + set environment variables

```bash
scripts/setup-coolify.sh
```

This creates the Docker Compose application in Coolify pointing to your GitHub repo and sets all environment variables via the Coolify API.

### C6. Push GitHub secrets

```bash
scripts/setup-github-secrets.sh
```

Sets `COOLIFY_WEBHOOK_URL`, `COOLIFY_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` so the deploy workflow can trigger Coolify and send notifications.

### C7. First deploy

Click **Deploy** in the Coolify UI, or trigger via API:

```bash
curl -X POST "$COOLIFY_WEBHOOK_URL" \
  -H "Authorization: Bearer $COOLIFY_TOKEN"
```

Monitor in Coolify → Application → Logs. First build takes ~5 min.

After deploy, run migrations in Coolify → Terminal (backend service):

```bash
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py createsuperuser
```

### C8. Register Stripe webhook

In the Stripe Dashboard → Webhooks → Add endpoint:

```
URL: https://api.YOUR_DOMAIN/api/v1/subscriptions/webhook/
Events: customer.subscription.* , invoice.* , checkout.session.completed
```

Copy the `whsec_...` signing secret → add to Coolify env as `STRIPE_WEBHOOK_SECRET` → redeploy.

### C9. Verify

```bash
scripts/verify-setup.sh
```

- [ ] `https://yourdomain.com` loads the landing page
- [ ] `https://api.yourdomain.com/health/` → `{"status":"ok"}`
- [ ] `https://api.yourdomain.com/api/docs/` loads Swagger UI
- [ ] `https://storage.yourdomain.com` loads MinIO console
- [ ] Registration, login, and email verification work
- [ ] Tenant subdomain `test-company.yourdomain.com` resolves
- [ ] Stripe checkout completes (test mode)
- [ ] Admin panel accessible at `https://api.yourdomain.com/<admin-url>/`

### C10. Configure Google OAuth callback

In GCP Console → OAuth 2.0 credentials → Authorised redirect URIs, add:

```
https://api.yourdomain.com/api/v1/auth/google/callback/
```

---

## Requirements for Claude to Run Phase C

```bash
which python3 ssh curl gh jq
gh auth status
```

Install any missing:
```bash
brew install gh jq
gh auth login
```
