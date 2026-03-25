# Setup Playbook

> Claude reads this file to execute the full initial setup of a new project.
> To trigger: tell Claude "do the initial setup" or "set up the project from scratch".

---

## What Claude Can Do Autonomously
- Rename the boilerplate to your project name
- Fill and validate environment files
- Install Coolify on the VPS via SSH
- Create DNS records in Cloudflare via API
- Push all secrets to GitHub via `gh secret set`
- Configure Coolify via its API
- Trigger the first deploy
- Run migrations remotely
- Verify everything is working

## Multi-Project Note

Most services support multiple projects under one account — you do NOT need a new account per project:

| Service | Reuse existing account? | Per-project action |
|---------|------------------------|-------------------|
| Stripe | ✅ Yes | Create new Products + Prices + webhook endpoint |
| Cloudflare | ✅ Yes | Add new domain (zone) to existing account |
| Sentry | ✅ Yes | Create new project in existing org → get new DSN |
| PostHog | ✅ Yes | Create new project in existing org → get new key |
| Resend | ✅ Yes | Verify new domain in existing account |
| Google OAuth | ✅ Yes | Create new GCP project under same Google account |
| Hetzner | ✅ Yes | Create new VPS (or reuse same VPS with Coolify) |
| Telegram | ✅ Yes | Reuse same bot, use a different chat/group per project |

---

## What You Must Do First (human-only)
These require accounts, credit cards, or browser flows that Claude cannot do:

### First project ever (~50 min)
| Task | Where |
|------|-------|
| Create Hetzner account + VPS | hetzner.com |
| Add domain to Cloudflare (new or existing account) | cloudflare.com |
| Create Stripe account | dashboard.stripe.com |
| Create Resend account | resend.com |
| Create Sentry account + org | sentry.io |
| Create PostHog account + org | posthog.com |
| Create Telegram bot | @BotFather on Telegram |

### Subsequent projects (~15 min)
| Task | Where |
|------|-------|
| Create new VPS on Hetzner (or reuse same VPS) | hetzner.com |
| Add new domain to Cloudflare | cloudflare.com |
| Create Stripe Products + Prices for this project | dashboard.stripe.com |
| Verify new domain in Resend | resend.com |
| Create new Sentry project in existing org | sentry.io |
| Create new PostHog project in existing org | posthog.com |
| Create new GCP project for Google OAuth | console.cloud.google.com |

**After that, Claude does the rest.**

---

## Step 0 — Gather All Credentials

Before starting, collect everything in one place. Claude will ask for these:

```
# Infrastructure
SERVER_IP=          # Hetzner VPS public IP
SSH_KEY_PATH=       # path to your SSH private key, e.g. ~/.ssh/id_ed25519

# Domain
DOMAIN=             # e.g. myapp.com
CLOUDFLARE_TOKEN=   # Cloudflare API token (Zone:Edit, DNS:Edit permissions)
CLOUDFLARE_ZONE_ID= # Cloudflare zone ID for your domain

# GitHub
GITHUB_REPO=        # e.g. username/my-saas

# App
APP_NAME=           # e.g. MyApp
ADMIN_EMAIL=        # your email (superuser)
ADMIN_PASSWORD=     # initial superuser password (change after first login)

# Services
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=     # get this AFTER webhook is registered (Step 6)
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=        # e.g. hello@myapp.com
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SENTRY_DSN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Secrets (Claude generates these)
SECRET_KEY=         # leave blank — Claude generates
POSTGRES_PASSWORD=  # leave blank — Claude generates
MINIO_ROOT_USER=    # leave blank — Claude generates
MINIO_ROOT_PASSWORD= # leave blank — Claude generates
ADMIN_URL=          # leave blank — Claude generates
```

---

## Claude's Setup Steps

### Step 1 — Rename the boilerplate

```bash
./new-project.sh
# Follow prompts to rename saas_boilerplate → your project name
```

### Step 2 — Generate secrets

Claude generates strong random values for:
```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_hex(24))")
MINIO_ROOT_USER=$(python3 -c "import secrets; print(secrets.token_hex(8))")
MINIO_ROOT_PASSWORD=$(python3 -c "import secrets; print(secrets.token_hex(24))")
ADMIN_URL=$(python3 -c "import secrets; print(secrets.token_hex(8))")
```

### Step 3 — Write environment files

Claude fills in:
- `backend/.env` — from `backend/.env.example`
- `.env` — root compose env, from `.env.example`

Using all credentials from Step 0 + generated secrets from Step 2.

### Step 4 — Configure DNS in Cloudflare

Claude calls the Cloudflare API to create all required DNS records:

```bash
scripts/setup-dns.sh
```

Records created:
- `A @ → SERVER_IP` (frontend)
- `A api → SERVER_IP` (backend)
- `A storage → SERVER_IP` (MinIO console)
- `A * → SERVER_IP` (tenant subdomains)

### Step 5 — Install Coolify on the VPS

```bash
ssh -i $SSH_KEY_PATH root@$SERVER_IP \
  "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash"
```

Wait ~3 minutes. Then verify:
```bash
curl -f http://$SERVER_IP:8000/api/v1/health
```

### Step 6 — Configure Coolify

Claude uses the Coolify API to:
1. Get the initial API token
2. Add the VPS as a server
3. Create a project
4. Create a Docker Compose application pointing to the GitHub repo
5. Set all environment variables
6. Configure domains for each service

```bash
scripts/setup-coolify.sh
```

### Step 7 — Push GitHub secrets

Claude pushes all secrets to GitHub so the deploy workflow works:

```bash
scripts/setup-github-secrets.sh
```

Secrets set:
- `COOLIFY_WEBHOOK_URL`
- `COOLIFY_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Step 8 — First deploy

```bash
# Trigger deploy via Coolify API
curl -X POST "$COOLIFY_WEBHOOK_URL" \
  -H "Authorization: Bearer $COOLIFY_TOKEN"
```

Wait for build to complete (~5 min). Monitor at `http://SERVER_IP:8000`.

### Step 9 — Run migrations and seed

```bash
ssh -i $SSH_KEY_PATH root@$SERVER_IP \
  "docker exec \$(docker ps -qf name=backend) uv run python manage.py migrate"

ssh -i $SSH_KEY_PATH root@$SERVER_IP \
  "docker exec \$(docker ps -qf name=backend) uv run python manage.py seed"

ssh -i $SSH_KEY_PATH root@$SERVER_IP \
  "docker exec -it \$(docker ps -qf name=backend) \
   uv run python manage.py createsuperuser \
   --email $ADMIN_EMAIL --noinput && \
   uv run python manage.py shell -c \
   \"from django.contrib.auth import get_user_model; \
   u=get_user_model().objects.get(email='$ADMIN_EMAIL'); \
   u.set_password('$ADMIN_PASSWORD'); u.save()\""
```

### Step 10 — Register Stripe webhook

```bash
# Get the webhook URL
echo "Register this URL in Stripe Dashboard → Webhooks:"
echo "https://api.$DOMAIN/api/v1/subscriptions/webhook/"
```

Claude opens the Stripe instructions and waits for the user to register the webhook and provide `STRIPE_WEBHOOK_SECRET`. Then updates `backend/.env` and redeploys.

### Step 11 — Verify everything

```bash
scripts/verify-setup.sh
```

Checks:
- [ ] `https://$DOMAIN` loads
- [ ] `https://api.$DOMAIN/health/` returns `{"status":"ok"}`
- [ ] `https://api.$DOMAIN/api/docs/` loads
- [ ] `https://storage.$DOMAIN` loads MinIO console
- [ ] Login works
- [ ] Admin panel accessible

### Step 12 — Report

Claude reports back:
- All URLs
- Admin credentials (remind to change password)
- What to do next (Stripe webhook secret, Google OAuth callback URL)

---

## Requirements for Claude to Run This

```bash
# All of these must be available in the shell:
which python3    # for secret generation
which ssh        # for VPS access
which curl       # for API calls
which gh         # for GitHub secrets (gh auth login must be done)
which jq         # for JSON parsing in scripts
```

Install missing tools:
```bash
brew install gh jq
gh auth login
```
