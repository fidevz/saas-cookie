# DEPLOYMENT

> Step-by-step guide to deploy this SaaS boilerplate to production.

---

## Recommended Stack

**All-in-one on a single VPS (recommended):** see `ops/COOLIFY_SETUP.md` for the full guide.

```
Hetzner VPS (€4.5/mo) + Coolify (free)
  ├── Frontend (Next.js)
  ├── Backend (Django ASGI)
  ├── Worker (Celery)
  ├── PostgreSQL
  ├── Redis
  └── MinIO (file storage)

Cloudflare (free) — DNS + CDN + wildcard SSL
```

## Alternative Infrastructure (managed services)

| Service | Recommended | Alternatives |
|---------|------------|-------------|
| Hosting | Coolify on Hetzner | Railway, Render, Fly.io |
| Database | PostgreSQL (bundled in Coolify) | Supabase, Neon, RDS |
| Redis | Redis (bundled in Coolify) | Upstash, Redis Cloud |
| File storage | MinIO (bundled in Coolify) | AWS S3, Cloudflare R2 |
| Email | Resend | SendGrid, Postmark |
| Error tracking | Sentry | — |
| DNS | Cloudflare | Route53 |

---

## Pre-Deployment Checklist

### Security
- [ ] `SECRET_KEY` is a strong random value (never the dev default)
- [ ] `DEBUG=False` in production
- [ ] `AUTH_COOKIE_SECURE=True`
- [ ] `ALLOWED_HOSTS` is set to your actual domain(s) only
- [ ] `CORS_ALLOWED_ORIGINS` is set to your frontend domain only
- [ ] Admin URL changed from default (`ADMIN_URL` env var)
- [ ] Stripe webhook secret configured and verified
- [ ] All secrets stored in environment variables, not in code

### Database
- [ ] Production database created
- [ ] `DATABASE_URL` pointing to production DB
- [ ] Migrations run: `python manage.py migrate`
- [ ] Initial data seeded if needed: `python manage.py seed`

### Infrastructure
- [ ] Redis instance running and `REDIS_URL` set
- [ ] Celery worker deployed and running
- [ ] Django Channels (Daphne/ASGI) configured — not WSGI
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Media file storage configured (S3/R2)

### External Services
- [ ] Stripe keys (live, not test)
- [ ] Stripe webhook endpoint registered at `[DOMAIN]/api/v1/subscriptions/webhook/`
- [ ] Google OAuth credentials configured for production domain
- [ ] Resend domain verified and API key set
- [ ] Sentry DSN configured
- [ ] PostHog project key set (if using)

### DNS
- [ ] Main domain pointing to frontend
- [ ] API subdomain (or path) pointing to backend
- [ ] Wildcard subdomain `*.yourdomain.com` → frontend (for tenant subdomains)
- [ ] SSL/TLS certificates active for all domains

---

## Deployment Steps

### 1. Backend

```bash
# Set all environment variables on your hosting platform

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (first deploy only)
python manage.py createsuperuser

# Start server (ASGI required for WebSockets)
uvicorn config.asgi:application --host 0.0.0.0 --port $PORT

# Start Celery worker (separate process)
celery -A config worker -l info

# Start Celery beat for scheduled tasks (if needed)
celery -A config beat -l info
```

### 2. Frontend

```bash
# Set environment variables:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

pnpm build
pnpm start     # serve with Node.js, or deploy to your preferred platform
```

> **Coolify (recommended):** The frontend is deployed automatically as part of the Docker Compose stack — no separate step needed. The deploy workflow triggers a Coolify webhook which rebuilds all services.
>
> If using an alternative provider (Railway, Render, Vercel), configure your frontend deploy step in `.github/workflows/deploy.yml`.

---

## Environment Variables — Production Values

### Backend (required for production)
```env
SECRET_KEY=<strong-random-50-char-string>
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_DOMAIN=.yourdomain.com   # leading dot — required for cross-subdomain auth cookies
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://...
BASE_DOMAIN=yourdomain.com
APP_NAME=YourAppName
ADMIN_URL=<secret-path>
RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=hello@yourdomain.com
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SENTRY_DSN=https://...@sentry.io/...
```

### Frontend (required for production)
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

---

## Post-Deploy Verification

After every deployment, verify:
- [ ] `/health/` returns 200
- [ ] Login works (email + Google)
- [ ] Stripe checkout completes (use test card in staging)
- [ ] WebSocket notifications connect
- [ ] Email sends (trigger a password reset)
- [ ] Admin panel accessible at custom URL
- [ ] Tenant subdomain resolves correctly

---

## Rollback

If a deployment fails:
1. Redeploy the previous version via your hosting platform
2. If migrations were run: assess whether they need to be reversed (`python manage.py migrate <app> <previous_migration>`)
3. Never reverse migrations in production without a database backup
4. Document the incident in `ops/INCIDENT_RESPONSE.md`

---

## Backups

### What gets backed up

| Data | Method | Destination |
|------|--------|-------------|
| PostgreSQL | `pg_dump \| gzip \| rclone rcat` | Cloudflare R2 |
| MinIO files | Not auto-backed up — use R2 bucket replication or `rclone sync` manually | — |
| Redis | Not backed up — fully ephemeral (Celery queues + cache) | — |

### Setup

**1. Create an R2 bucket** named `backups` (or your preference) in the Cloudflare dashboard.

**2. Create an R2 API token** with Object Read & Write permissions scoped to that bucket. Note the Access Key ID, Secret Access Key, and endpoint URL (`https://<account-id>.r2.cloudflarestorage.com`).

**3. Add to your `.env`:**
```env
BACKUP_SCHEDULE=0 2 * * *      # daily at 2am UTC (cron syntax)
BACKUP_RETENTION_DAYS=7
R2_BUCKET=backups
R2_ACCESS_KEY=<r2-access-key-id>
R2_SECRET_KEY=<r2-secret-access-key>
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
```

The `backup` service in `docker-compose.yml` starts automatically with the rest of the stack. Backup files are stored at `postgres/postgres_YYYYMMDD_HHMMSS.sql.gz` in the R2 bucket. Files older than `BACKUP_RETENTION_DAYS` are pruned automatically after each run.

### Triggering a manual backup

```bash
docker compose exec backup /backup.sh
```

### Restoring from backup

```bash
# 1. Download the backup file from R2
rclone copy r2:backups/postgres/postgres_YYYYMMDD_HHMMSS.sql.gz ./

# 2. Restore into the running database container
gunzip -c postgres_YYYYMMDD_HHMMSS.sql.gz \
  | docker compose exec -T db \
    psql -U postgres saas_boilerplate
```

> Always take a fresh backup before restoring, and test restores in staging first.

### Verifying backups

After the first scheduled run, confirm the file appeared in R2:
```bash
docker compose exec backup \
  rclone ls r2:${R2_BUCKET}/postgres
```

---

## Staging Environment

Always maintain a staging environment that mirrors production:
- Same infrastructure, smaller size
- Use Stripe test keys (never live keys in staging)
- Separate database and Redis
- Separate Sentry project
- Test every deploy in staging before production
