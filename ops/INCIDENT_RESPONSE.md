# INCIDENT RESPONSE

> What to do when something breaks in production.
> Stay calm. Follow the process. Fix first, blame never.

---

## Severity Levels

| Level | Definition | Response time | Example |
|-------|-----------|--------------|---------|
| P0 — Critical | Service completely down or data loss | Immediate | 500 errors for all users, database unreachable |
| P1 — High | Major feature broken for all users | < 1 hour | Login broken, payments failing, WebSockets down |
| P2 — Medium | Feature broken for some users | < 4 hours | Specific plan feature broken, email not sending |
| P3 — Low | Minor issue, workaround exists | < 24 hours | UI bug, slow endpoint, non-critical error spike |

---

## Incident Response Steps

### Step 1 — Detect
Sources of alerts:
- Sentry: error rate spike or new critical errors
- Uptime monitor: `/health/` endpoint down
- User reports via support
- Failed Celery tasks
- Stripe webhook failures

### Step 2 — Assess (first 5 minutes)
Answer these questions:
1. What is broken? (which feature/endpoint/service)
2. Who is affected? (all users, specific plan, specific tenant)
3. Since when? (check Sentry first occurrence, deploy history)
4. Is it getting worse, stable, or improving?

### Step 3 — Communicate
- Update status page (if you have one) within 10 minutes of P0/P1
- Notify team via [Telegram/Slack] immediately for P0/P1
- Do NOT wait until it's fixed to communicate — users deserve to know

**Status page update template:**
```
[TIME] Investigating — We are aware of an issue affecting [feature].
We are actively investigating and will provide updates every 30 minutes.
```

### Step 4 — Mitigate (stop the bleeding)
Before fixing root cause, reduce impact:
- **Feature flag off:** use `FEATURE_*` flags to disable broken feature
- **Rollback:** redeploy previous version if issue was introduced by a deploy
- **Scale up:** if load-related, add instances
- **Database:** if DB issue, check connections, locks, long-running queries
- **Redis:** if Celery/Channels down, check Redis health

### Step 5 — Fix
- Fix in a branch, not directly on main
- Deploy to staging first if time allows
- For P0: speed > process — push to production if staging step would take too long

### Step 6 — Verify
- Confirm the specific issue is resolved
- Run post-deploy verification checklist from `DEPLOYMENT.md`
- Watch Sentry for 15 minutes after fix
- Confirm with any affected users

### Step 7 — Post-mortem (within 24 hours for P0/P1)
Write a brief post-mortem in `ops/POST_MORTEMS.md`:
- What happened
- Timeline
- Root cause
- What we fixed
- What we're doing to prevent recurrence

---

## Common Incidents & Quick Fixes

### Backend returns 500 errors
1. Check Sentry for the specific error and stack trace
2. Check recent deploys — did this start after a deploy?
3. Check DB connections: `SELECT count(*) FROM pg_stat_activity;`
4. Check Redis: `redis-cli ping`
5. Check Celery worker logs

### Login broken
1. Check `authentication` app for errors in Sentry
2. Verify JWT settings haven't changed (`SECRET_KEY` must be stable)
3. Check `allauth` and `dj-rest-auth` for errors
4. Test with email + Google separately to isolate

### Stripe webhooks failing
1. Check Stripe Dashboard → Webhooks for failed deliveries
2. Verify `STRIPE_WEBHOOK_SECRET` is correct in production
3. Check `/api/v1/subscriptions/webhook/` endpoint is accessible
4. Check Sentry for webhook processing errors
5. Stripe will retry failed webhooks — events won't be lost

### WebSockets not connecting
1. Verify Daphne (ASGI) is running, not Gunicorn (WSGI)
2. Check Redis is reachable from the backend
3. Check `CHANNEL_LAYERS` config points to correct Redis
4. Verify WebSocket URL in frontend env (`NEXT_PUBLIC_WS_URL`) uses `wss://`

### Emails not sending
1. Check Resend dashboard for failed deliveries
2. Verify `RESEND_API_KEY` is valid
3. Check domain verification in Resend
4. Check Celery worker is running (emails may be sent async)

### Celery tasks stuck
1. Check Redis is running: `redis-cli ping`
2. Restart Celery worker
3. Check for tasks stuck in `STARTED` state: purge if necessary
4. Check for memory issues on the worker process

---

## Monitoring Checklist (daily)

- [ ] Sentry: any new P0/P1 errors?
- [ ] Uptime: all endpoints green?
- [ ] Celery: no stuck or failed tasks?
- [ ] Stripe: webhook success rate 100%?
- [ ] Database: connection pool healthy?
