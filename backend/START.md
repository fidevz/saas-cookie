# SaaS Boilerplate — Backend

A production-ready Django REST API with multi-tenancy, JWT auth, Stripe billing, WebSockets, and Celery.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/) |
| Redis | 7+ | `brew install redis` or Docker |

---

## 1. Installation

```bash
cd backend/
uv sync
```

This creates a `.venv` and installs all dependencies (including dev dependencies).

---

## 2. Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key — generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `STRIPE_SECRET_KEY` | For billing | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | For billing | Stripe webhook signing secret |
| `RESEND_API_KEY` | For email | Resend API key |
| `GOOGLE_CLIENT_ID` | For OAuth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For OAuth | Google OAuth client secret |
| `SENTRY_DSN` | For production | Sentry error tracking DSN |

For local development, set:
```
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
```

---

## 3. Database Setup

```bash
make db-create      # createdb saas_boilerplate
make migrate        # apply all migrations
make seed           # create test data
```

The seed command creates:
- Plans: **Starter** ($9/mo) and **Pro** ($29/mo, 14-day trial)
- Test user: `admin@test.com` / `testpassword123` (superuser)
- Test tenant: `test-company`

---

## 4. Running the Server

In two separate terminals:

**Terminal 1 — API server:**
```bash
make run
# or: uv run uvicorn config.asgi:application --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Celery worker:**
```bash
make worker
# or: uv run celery -A config worker -l info
```

Redis must be running for Celery and WebSocket channel layers.

---

## 5. Running Tests

```bash
make test
# or: uv run pytest
```

Run a specific test file:
```bash
uv run pytest apps/users/tests/test_views.py -v
```

Run with coverage:
```bash
uv run pytest --cov=apps --cov-report=html
```

---

## 6. Code Quality

```bash
make lint    # check style (ruff)
make fmt     # auto-fix style (ruff)
```

Install pre-commit hooks (optional but recommended):
```bash
uv run pre-commit install
```

---

## 7. API Documentation

With the server running:

- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/
- **Health check**: http://localhost:8000/health/

---

## 8. Admin Panel

- **URL**: http://localhost:8000/tacomate/
- **Login**: `admin@test.com` / `testpassword123` (after `make seed`)

The admin URL is configurable via the `ADMIN_URL` environment variable (default: `tacomate`).

---

## 9. Stripe Configuration

### Webhook Endpoint

Register in the [Stripe Dashboard](https://dashboard.stripe.com/webhooks):

```
https://yourdomain.com/api/v1/subscriptions/webhook/
```

Events to subscribe to:
- `checkout.session.completed`
- `invoice.paid`
- `customer.subscription.updated`
- `customer.subscription.deleted`

### Local Development with Stripe CLI

```bash
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook/
```

Copy the webhook signing secret and set `STRIPE_WEBHOOK_SECRET` in `.env`.

---

## 10. Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID
3. Add authorized redirect URI: `https://yourdomain.com/api/v1/auth/google/`
4. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
5. In Django admin → Social Applications → Add a Google application

---

## 11. Feature Flags

Control features via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FEATURE_TEAMS` | `true` | Team invitation and member management |
| `FEATURE_BILLING` | `true` | Stripe subscription management |
| `FEATURE_NOTIFICATIONS` | `true` | In-app notifications + WebSocket |

All flags are exposed at `GET /api/v1/features/` (public endpoint).

---

## 12. Multi-Tenancy

The API uses subdomain-based tenant resolution. The `TenantMiddleware` reads the `Host` header and sets `request.tenant`.

### Local Development

Add entries to `/etc/hosts` for subdomain testing:

```
127.0.0.1  test-company.localhost
127.0.0.1  acme.localhost
```

Then access the API at:
```
http://test-company.localhost:8000/api/v1/tenants/current/
```

### Row-Level Isolation

All tenant-scoped queries must filter by tenant. Use the provided mixins:

```python
from apps.tenants.mixins import TenantModelMixin, TenantViewMixin
```

Custom permissions:
- `IsTenantMember` — user must be a member of `request.tenant`
- `IsTenantAdmin` — user must be an admin of `request.tenant`
- `IsSubscriptionActive` — tenant must have an active subscription
- `FeatureEnabled("TEAMS")` — feature flag must be enabled

---

## 13. WebSocket Notifications

Connect via:

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${accessToken}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'notification') {
    console.log(data.notification);
  }
};

// Mark a notification as read
ws.send(JSON.stringify({ action: 'mark_read', notification_id: 42 }));
```

---

## 14. API Endpoints Reference

### Auth (`/api/v1/auth/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `register/` | Create account + tenant |
| POST | `login/` | Authenticate, get tokens |
| POST | `logout/` | Blacklist refresh token |
| POST | `token/refresh/` | Exchange cookie for new access token |
| POST | `google/` | Google OAuth login |
| POST | `password-reset/` | Request reset email |
| POST | `password-reset/confirm/` | Confirm reset with token |

### Users (`/api/v1/users/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `me/` | Get own profile |
| PATCH | `me/` | Update own profile |

### Tenants (`/api/v1/tenants/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `current/` | Get current tenant |
| PATCH | `current/` | Update current tenant |
| GET | `members/` | List members |

### Teams (`/api/v1/teams/`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `invitations/` | Invite a member |
| GET | `members/` | List members |
| PATCH | `members/{id}/` | Update member role |
| DELETE | `members/{id}/remove/` | Remove member |
| POST | `accept-invite/{token}/` | Accept invitation |

### Notifications (`/api/v1/notifications/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `` (root) | List notifications |
| PATCH | `{id}/read/` | Mark one as read |
| POST | `read-all/` | Mark all as read |

### Subscriptions (`/api/v1/subscriptions/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `plans/` | List available plans (public) |
| POST | `checkout/` | Create Stripe checkout session |
| POST | `portal/` | Create Stripe customer portal session |
| POST | `cancel/` | Cancel subscription at period end |
| POST | `webhook/` | Stripe webhook receiver |

---

## 15. Project Structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── development.py  # Local dev overrides
│   │   └── production.py   # Production + Sentry
│   ├── asgi.py             # ASGI + Channels
│   ├── celery.py           # Celery app
│   ├── routing.py          # WebSocket URL routing
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI (fallback)
├── apps/
│   ├── core/               # Base models, feature flags, audit log
│   ├── users/              # CustomUser model
│   ├── authentication/     # JWT auth, Google OAuth, password reset
│   ├── tenants/            # Multi-tenancy: Tenant, TenantMembership
│   ├── teams/              # Invitations, member management
│   ├── notifications/      # In-app notifications + WebSocket consumer
│   └── subscriptions/      # Stripe billing: Plan, Subscription
├── utils/
│   ├── audit.py            # log_action() helper
│   ├── email.py            # ResendEmailBackend + send_email()
│   ├── health.py           # /health/ endpoint
│   ├── permissions.py      # IsTenantMember, IsTenantAdmin, etc.
│   └── throttling.py       # LoginThrottle, RegisterThrottle
├── locale/
│   ├── en/                 # English translations
│   └── es/                 # Spanish translations
├── .env.example
├── .pre-commit-config.yaml
├── conftest.py             # pytest fixtures
├── Makefile
├── manage.py
├── Procfile
└── pyproject.toml
```
