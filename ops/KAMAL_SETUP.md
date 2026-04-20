# Kamal Setup Guide

> Deploy the entire stack (frontend, backend, worker, DB, Redis, MinIO) on a single VPS using Kamal 2.
> Images are built in GitHub Actions and pushed to GHCR. Kamal pulls them onto the server.

---

## 1. Provision the VPS (Hetzner)

1. Create account at [hetzner.com](https://hetzner.com)
2. New project → Add server:
   - **Location:** Closest to your users (Ashburn for US, Falkenstein for EU)
   - **Image:** Ubuntu 24.04
   - **Type:** CX22 (2 vCPU, 4GB RAM) to start — upgrade later if needed
   - **Networking:** Enable public IPv4
   - **SSH key:** Add your key — Kamal will use this to connect
3. Note the server IP

---

## 2. Prepare the Server

SSH in and make sure Docker is installed:

```bash
ssh root@YOUR_SERVER_IP

# Install Docker if not already present
curl -fsSL https://get.docker.com | sh

# Create data directories for Kamal accessory volumes
mkdir -p /var/lib/YOUR_APP_NAME/{postgres,redis,minio}

# Verify SSH works from your local machine
exit
ssh root@YOUR_SERVER_IP docker ps  # should return empty table
```

Kamal manages everything else on the server via SSH.

---

## 3. Configure DNS (Cloudflare)

In Cloudflare, point all records to your VPS IP:

| Type | Name | Value | Proxy |
|------|------|-------|-------|
| A | `@` | `YOUR_SERVER_IP` | ✅ Orange cloud |
| A | `api` | `YOUR_SERVER_IP` | ✅ Orange cloud |
| A | `*` | `YOUR_SERVER_IP` | ✅ Orange cloud (wildcard for tenants) |

Cloudflare handles SSL termination. Kamal's `kamal-proxy` handles routing.

---

## 4. Set Up GHCR (Container Registry)

Kamal builds images on GitHub Actions and pushes them to GHCR.

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a token with `write:packages` and `read:packages` scopes
3. Test locally:
   ```bash
   echo YOUR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

---

## 5. Update Kamal Config

Edit `deploy/config/deploy.yml` and `deploy/config/deploy.frontend.yml`:

1. Replace `YOUR_APP_NAME` with your project name (e.g. `myapp`)
2. Replace `YOUR_GITHUB_ORG` with your GitHub username or org
3. Replace `YOUR_SERVER_IP` with your VPS IP address
4. Replace `yourdomain.com` with your actual domain
5. Set build args in `deploy.frontend.yml` (Stripe publishable key, Turnstile site key)

---

## 6. Add GitHub Secrets

In your GitHub repo → Settings → Secrets and variables → Actions, add:

### Infrastructure
| Secret | Value |
|--------|-------|
| `VPS_SSH_PRIVATE_KEY` | SSH private key for the VPS |
| `KAMAL_REGISTRY_PASSWORD` | GitHub PAT with `write:packages` scope |

### Application
| Secret | Value |
|--------|-------|
| `SECRET_KEY` | Django secret key (50+ random chars) |
| `DATABASE_URL` | `postgres://postgres:<POSTGRES_PASSWORD>@YOUR_APP_NAME-backend-db:5432/YOUR_APP_NAME` |
| `REDIS_URL` | `redis://:<REDIS_PASSWORD>@YOUR_APP_NAME-backend-redis:6379/0` |
| `POSTGRES_PASSWORD` | Strong random password |
| `REDIS_PASSWORD` | Strong random password |
| `ALLOWED_HOSTS` | `api.yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | `https://yourdomain.com` |
| `ADMIN_URL` | Custom admin path (default: `tacomate`) |
| `FRONTEND_URL` | `https://yourdomain.com` |
| `SUPPORT_EMAIL` | Support email address |
| `AUTH_COOKIE_DOMAIN` | `.yourdomain.com` |

### External services
| Secret | Value |
|--------|-------|
| `STRIPE_SECRET_KEY` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` |
| `STRIPE_PUBLISHABLE_KEY` | `pk_live_...` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `RESEND_API_KEY` | `re_...` |
| `DEFAULT_FROM_EMAIL` | `hello@yourdomain.com` |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret key |
| `SENTRY_DSN` | Sentry DSN (optional) |

### MinIO + storage
| Secret | Value |
|--------|-------|
| `MINIO_ROOT_USER` | Strong username |
| `MINIO_ROOT_PASSWORD` | Strong password |
| `AWS_STORAGE_BUCKET_NAME` | `media` |

### Backups (Cloudflare R2)
| Secret | Value |
|--------|-------|
| `R2_BUCKET` | R2 bucket name |
| `R2_ACCESS_KEY` | R2 access key |
| `R2_SECRET_KEY` | R2 secret key |
| `R2_ENDPOINT` | `https://<account-id>.r2.cloudflarestorage.com` |

### Frontend build args (baked into Next.js image)
| Secret | Value |
|--------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com/api/v1` |
| `NEXT_PUBLIC_WS_URL` | `wss://api.yourdomain.com` |

### Notifications
| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |

---

## 7. Install Kamal Locally

```bash
gem install kamal

# Verify
kamal version   # should show 2.x.x
```

---

## 8. First-time Deploy

From the repo root:

```bash
cd deploy

# Copy and fill in secrets for local use
cp .env.kamal .env
# Edit .env with your values

# Boot kamal-proxy + accessories + app (backend)
kamal setup

# Boot frontend
kamal setup -c config/deploy.frontend.yml
```

`kamal setup` will:
1. Install `kamal-proxy` on the server
2. Boot all accessories (db, redis, minio, backup)
3. Build the Docker image (pushed to GHCR)
4. Pull the image on the server and start containers

### After first deploy

```bash
# Run migrations (if before_switch hook didn't run yet)
kamal app exec -i 'uv run python manage.py migrate'

# Seed initial data
kamal app exec -i 'uv run python manage.py seed'

# Create superuser
kamal app exec -i 'uv run python manage.py createsuperuser'

# Initialize MinIO bucket
kamal accessory exec minio bash
# Inside minio container:
# mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
# mc mb --ignore-existing local/media
# exit
```

---

## 9. Verify Everything Works

- [ ] `https://yourdomain.com` loads the frontend
- [ ] `https://api.yourdomain.com/health/` returns `{"status":"ok","db":"ok","redis":"ok"}`
- [ ] Login works
- [ ] File upload stores in MinIO
- [ ] Stripe webhook reachable at `https://api.yourdomain.com/api/v1/subscriptions/webhook/`
- [ ] Tenant subdomain `test-company.yourdomain.com` resolves correctly

---

## Day-to-day Commands

```bash
# From deploy/ directory

kamal deploy                                    # deploy backend
kamal deploy -c config/deploy.frontend.yml      # deploy frontend

kamal rollback                                  # rollback backend
kamal rollback -c config/deploy.frontend.yml    # rollback frontend

kamal details                                   # show all running containers
kamal app logs -f                               # tail backend logs
kamal app logs -f --roles=worker                # tail worker logs
kamal app exec -i bash                          # open shell in web container
kamal app exec -i 'uv run python manage.py shell_plus'

kamal accessory logs db                         # postgres logs
kamal accessory logs backup                     # backup cron logs
kamal accessory exec minio bash                 # shell in minio

kamal lock release                              # release a stuck deploy lock
kamal proxy logs                                # kamal-proxy routing logs
```

---

## Stripe Webhooks

Update your Stripe webhook endpoint to:
```
https://api.yourdomain.com/api/v1/subscriptions/webhook/
```

For local testing:
```bash
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook/
```

---

## Scaling Up

When traffic grows:

| Bottleneck | Fix |
|-----------|-----|
| CPU/RAM | Upgrade Hetzner plan |
| DB performance | Move PostgreSQL to managed (Supabase or Neon) |
| Worker throughput | Increase `--concurrency` in `deploy.yml` worker role |
| Global latency | Cloudflare CDN is already configured |
