# MONITORING

> What to watch, how to watch it, and what to do when something looks wrong.

---

## Stack

| Tool | Purpose | Setup required |
|------|---------|---------------|
| **Sentry** | Error tracking + performance | Add `SENTRY_DSN` to env |
| **PostHog** | Product analytics + session replay | Add `POSTHOG_API_KEY` to env |
| **UptimeRobot / Better Uptime** | Uptime monitoring + alerts | Configure externally |
| **Stripe Dashboard** | Payment health + webhook delivery | Always-on |
| **GA4** | Web traffic | Add GA4 tag to frontend |

---

## Sentry Setup

### Backend

Sentry is already installed (`sentry-sdk[django]`). Activate it by setting `SENTRY_DSN` in your production environment.

`config/settings/production.py` initializes it automatically:
```python
import sentry_sdk
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=0.1,   # 10% of transactions for performance
    profiles_sample_rate=0.1,
)
```

### Frontend

Install and initialize in `src/app/layout.tsx`:
```bash
pnpm add @sentry/nextjs
pnpm dlx @sentry/wizard@latest -i nextjs
```

### Sentry Alerts to configure

Set these up in your Sentry project → Alerts:

| Alert | Condition | Action |
|-------|-----------|--------|
| High error rate | Error rate > 5/min | Email + Telegram |
| New issue | First occurrence of any issue | Email |
| P0 spike | Error rate > 50/min | Telegram (urgent) |
| Performance regression | p95 latency > 2s | Email |
| Unhandled exception in Celery | Any | Email |

---

## Uptime Monitoring

Monitor these endpoints externally (UptimeRobot free tier covers this):

| Endpoint | Check interval | Alert if down |
|----------|---------------|--------------|
| `https://yourdomain.com` | 5 min | Immediately |
| `https://api.yourdomain.com/health/` | 1 min | Immediately |
| `https://api.yourdomain.com/api/v1/subscriptions/plans/` | 5 min | After 2 failures |

**`/health/` returns:**
```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok"
}
```
Alert if any field is not `"ok"` or if the endpoint returns non-200.

---

## Key Metrics to Watch

### Daily (quick scan — 5 minutes)
- Sentry: any new P0/P1 issues?
- Uptime: all green?
- Stripe: webhook success rate at 100%?
- Celery: any stuck or failed tasks?

### Weekly
- Error rate trend (up or down vs. last week?)
- API p95 latency (Sentry performance)
- New user signups (GA4 + PostHog)
- Trial-to-paid conversions (Stripe)
- Churn (Stripe MRR movement)

### Monthly
- Full infrastructure cost review
- Dependency audit: `uv run pip-audit`
- Database size growth rate
- Redis memory usage trend

---

## PostHog Setup

PostHog is in `pyproject.toml` dependencies. To activate:

**Backend** — uncomment in `config/settings/base.py`:
```python
POSTHOG_API_KEY = config("POSTHOG_API_KEY", default="")
POSTHOG_HOST = config("POSTHOG_HOST", default="https://app.posthog.com")
```

**Frontend** — add to `src/app/layout.tsx`:
```tsx
import posthog from 'posthog-js'
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
})
```

### Events to track (minimum viable)
```
user_registered
trial_started
subscription_started
subscription_cancelled
feature_used (with feature_name property)
```

---

## Database Monitoring

### Connections
Watch `pg_stat_activity` for connection pool exhaustion:
```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```
Alert if active connections > 80% of `max_connections`.

### Slow queries
Enable `pg_stat_statements` on your PostgreSQL instance.
Review weekly — any query taking > 500ms needs an index or optimization.

### Storage growth
Check DB size monthly:
```sql
SELECT pg_size_pretty(pg_database_size('your_db_name'));
```

---

## Redis Monitoring

Watch for:
- Memory usage approaching `maxmemory` limit
- Celery queue depth: `redis-cli llen celery` — alert if > 1000

```bash
redis-cli info memory | grep used_memory_human
redis-cli llen celery
```

---

## Celery Monitoring

### Check worker status
```bash
celery -A config inspect active
celery -A config inspect reserved
```

### Failed tasks
Failed tasks are logged to Sentry. Additionally, review:
```bash
celery -A config events   # real-time task stream
```

Consider adding [Flower](https://flower.readthedocs.io/) for a web UI dashboard for Celery monitoring in production.

---

## Stripe Monitoring

Check weekly in the Stripe Dashboard:
- **Webhooks** → Success rate should be 100%. Investigate any failures.
- **Radar** → Review flagged payments
- **Revenue** → MRR, churn, net revenue retention

Set up Stripe email alerts for:
- Disputed charges
- Webhook delivery failures
- Significant revenue changes

---

## Alerting Channels

| Severity | Channel | Response |
|----------|---------|---------|
| P0 (service down) | Telegram (immediate) | Drop everything |
| P1 (major feature broken) | Telegram + Email | Within 1 hour |
| P2 (minor issue) | Email | Within 4 hours |
| P3 (slow degradation) | Weekly review | Scheduled fix |

Telegram Bot for alerts: configure in `marketing/decisions/ESCALATION.md`.
