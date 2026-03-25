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

npm run build
npm run start  # or deploy to Vercel
```

---

## Environment Variables — Production Values

### Backend (required for production)
```env
SECRET_KEY=<strong-random-50-char-string>
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
AUTH_COOKIE_SECURE=True
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

## Staging Environment

Always maintain a staging environment that mirrors production:
- Same infrastructure, smaller size
- Use Stripe test keys (never live keys in staging)
- Separate database and Redis
- Separate Sentry project
- Test every deploy in staging before production
