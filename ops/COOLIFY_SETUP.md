# Coolify Setup Guide

> Deploy the entire stack (frontend, backend, worker, DB, Redis, MinIO) on a single VPS using Coolify.
> No Docker registry needed — Coolify builds images directly from GitHub.

---

## 1. Provision the VPS (Hetzner)

1. Create account at [hetzner.com](https://hetzner.com)
2. New project → Add server:
   - **Location:** Closest to your users (Ashburn for US, Falkenstein for EU)
   - **Image:** Ubuntu 24.04
   - **Type:** CX22 (2 vCPU, 4GB RAM) to start — upgrade later if needed
   - **Networking:** Enable public IPv4
   - Add your SSH key
3. Note the server IP

---

## 2. Install Coolify

SSH into the server and run the official installer:

```bash
ssh root@YOUR_SERVER_IP

curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Installation takes ~3 minutes. When done, access Coolify at:
```
http://YOUR_SERVER_IP:8000
```

Create your admin account and follow the onboarding wizard.

---

## 3. Connect Your Server to Coolify

In the onboarding, Coolify installs itself on the same server (localhost). Accept the default — it works perfectly for a single-VPS setup.

---

## 4. Connect GitHub

Coolify Dashboard → Sources → Add → GitHub App

Follow the prompts to install the Coolify GitHub App on your repository. This allows Coolify to pull code and set up webhooks.

---

## 5. Configure DNS (Cloudflare)

Before deploying, set up DNS. In Cloudflare:

| Type | Name | Value | Notes |
|------|------|-------|-------|
| A | `@` | `YOUR_SERVER_IP` | Root domain → frontend |
| A | `api` | `YOUR_SERVER_IP` | API |
| A | `storage` | `YOUR_SERVER_IP` | MinIO console |
| A | `*` | `YOUR_SERVER_IP` | Wildcard for tenant subdomains |

Enable **Proxy (orange cloud)** on all records for Cloudflare CDN + SSL.

---

## 6. Create the Application in Coolify

Coolify Dashboard → Projects → New Project → Add Resource → **Docker Compose**

Configure:
- **Repository:** your GitHub repo
- **Branch:** `main`
- **Docker Compose location:** `docker-compose.yml` (root of repo)
- **Build on server:** ✅ Yes (no registry needed)

---

## 7. Set Environment Variables in Coolify

In the application settings → Environment Variables, add:

### Compose-level (top-level `.env`)
```env
POSTGRES_DB=your_project_name   # must match DATABASE_URL below
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<strong-random-password>

NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

MINIO_ROOT_USER=<strong-username>
MINIO_ROOT_PASSWORD=<strong-password>
MINIO_BUCKET=media
```

### Backend `.env`
**Use Coolify's "Env File" feature** to paste the content below directly into the Coolify UI — it mounts it as a file inside the container without ever touching the git repo. Do not commit `.env` files to git, even gitignored ones.

```env
SECRET_KEY=<50-char-random-string>
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
AUTH_COOKIE_SECURE=True

DATABASE_URL=postgres://postgres:<POSTGRES_PASSWORD>@db:5432/your_project_name   # must match POSTGRES_DB above
REDIS_URL=redis://redis:6379/0

BASE_DOMAIN=yourdomain.com
APP_NAME=YourApp
ADMIN_URL=<secret-path>

RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=hello@yourdomain.com

STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

SENTRY_DSN=https://...@sentry.io/...

USE_S3=True
MINIO_ROOT_USER=<same-as-above>
MINIO_ROOT_PASSWORD=<same-as-above>
MINIO_BUCKET=media
MINIO_ENDPOINT=http://minio:9000
MINIO_PUBLIC_URL=https://storage.yourdomain.com/media
```

> **Note:** `FRONTEND_URL` should be set to your root domain (e.g. `https://yourdomain.com`) — this is used to build email confirmation links.

---

## 8. Configure Domains in Coolify

In the application → Domains, assign:

| Service | Domain |
|---------|--------|
| `frontend` | `yourdomain.com` |
| `backend` | `api.yourdomain.com` |
| `minio` (port 9001) | `storage.yourdomain.com` |

Coolify handles Let's Encrypt SSL automatically via Traefik. ✅

---

## 9. Deploy for the First Time

Click **Deploy** in Coolify.

Coolify will:
1. Pull code from GitHub
2. Build all images on the server (takes ~3–5 min first time)
3. Start all containers
4. Issue SSL certificates

After deploy, run migrations:

In Coolify → Terminal (backend service):
```bash
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py createsuperuser
```

---

## 10. Set Up GitHub Release → Auto Deploy

### Get your Coolify webhook

In Coolify → Application → Webhooks → copy the **Deploy Webhook URL** and **API Token**.

### Add secrets to GitHub

In your GitHub repo → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `COOLIFY_WEBHOOK_URL` | Coolify deploy webhook URL |
| `COOLIFY_TOKEN` | Coolify API token |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### Deploy flow

From now on:
```
git tag v1.0.0
git push origin v1.0.0

# Then on GitHub: Releases → Draft new release → publish
# → GitHub Action triggers automatically
# → Coolify pulls latest code, rebuilds, redeploys
# → You get a Telegram notification when done
```

---

## 11. Verify Everything Works

After first deploy:

- [ ] `https://yourdomain.com` loads the frontend
- [ ] `https://api.yourdomain.com/health/` returns `{"status":"ok"}`
- [ ] `https://api.yourdomain.com/api/docs/` loads Swagger UI
- [ ] `https://storage.yourdomain.com` loads MinIO Console
- [ ] Login works
- [ ] File upload stores in MinIO (check MinIO console bucket)
- [ ] Stripe webhook reachable at `https://api.yourdomain.com/api/v1/subscriptions/webhook/`
- [ ] Tenant subdomain `test-company.yourdomain.com` resolves correctly (wildcard DNS)

---

## Running Multiple Projects on One VPS

Coolify was designed for this. You can run multiple SaaS projects on the same server:

```
Hetzner CX32 (€8.5/mo, 4 vCPU 8GB)
  └── Coolify
        ├── Project A (frontend + backend + worker + db + redis + minio)
        ├── Project B (frontend + backend + worker + db + redis + minio)
        └── Project C ...
```

Each project gets its own:
- Docker network (isolated)
- Domains and SSL certs (Traefik handles all of them)
- Environment variables
- Volumes (data is never shared between projects)

**Practical limits on a CX32 (€8.5/mo):**
- 2–3 small/medium SaaS projects comfortably
- Upgrade to CX52 (€16/mo) for 4–6 projects

**When to use a separate VPS per project:**
- Project has significant traffic (>10k users)
- Compliance requires full isolation
- One project's failure cannot affect others

---

## Scaling Up (single project)

When traffic grows:

| Bottleneck | Fix |
|-----------|-----|
| CPU/RAM | Upgrade Hetzner plan (CX32 = €8.5/mo) |
| DB performance | Move PostgreSQL to managed (Supabase or Neon) |
| File storage | MinIO scales with disk — add a volume |
| Worker throughput | Increase `--concurrency` in worker command |
| Global latency | Add Cloudflare CDN (already configured via DNS) |

---

## Useful Coolify Tips

- **Logs:** Coolify → Application → Logs — real-time log streaming
- **Terminal:** Coolify → Application → Terminal — run commands inside any container
- **Backups:** Coolify → Databases → your PostgreSQL → Backups — set up automatic backups
- **Rollback:** Coolify keeps the last N deployments — one click to rollback
