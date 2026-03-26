# Blocking Issues

Code-level problems that must be fixed before launching to real users. Unlike the launch checklist (`ops/LAUNCH_CHECKLIST.md`), which covers configuration and process, these require actual code changes.

---

## 1. Stripe Webhook Idempotency

**Risk:** Double-billing, double-provisioning, or double-cancelling subscriptions.

Stripe retries webhook delivery on any non-2xx response, and network failures can cause the same event to be delivered more than once. The current handlers in `backend/apps/subscriptions/webhooks.py` have no deduplication — `_handle_checkout_completed` uses `get_or_create` (partially safe), but `_handle_invoice_paid` and `_handle_subscription_deleted` will apply their changes multiple times if retried.

**Fix:** Store processed Stripe event IDs in a `ProcessedWebhookEvent(event_id, processed_at)` table. At the top of `handle_webhook()`, check if `event["id"]` already exists and return early if so. This is especially critical for `invoice.payment_succeeded` and `customer.subscription.deleted`.

---

## 2. WebSocket JWT Exposed in Query String

**Risk:** Access tokens appear in server access logs, proxy logs, and browser history.

The WebSocket client in `frontend/src/lib/ws.ts` connects to `ws://host/ws/notifications/?token=<jwt>`. Any token that appears in a URL is likely to be logged by Nginx, Coolify, and any reverse proxy in the stack. JWT access tokens are short-lived (5 min) but this is still a security exposure.

**Fix:** Connect without the token in the URL, then send it as the first WebSocket message. Update `NotificationConsumer` in `backend/apps/notifications/consumers.py` to authenticate from the first received message and close the connection (code 4001) if no valid token arrives within a short timeout (e.g. 5 seconds).

---

## 3. Plan Limits Not Enforced

**Risk:** Users on free or lower-tier plans can exceed their seat limit at no charge.

The `team_members` integer capability exists in `backend/apps/subscriptions/capabilities.py` and is snapshotted on each `Subscription`, but `InviteMemberView` and `AcceptInviteView` in `backend/apps/teams/views.py` never read it. A tenant on a 1-seat plan can invite unlimited members.

**Fix:** In both views, fetch the tenant's active subscription capabilities, compare `team_members` against the current member count, and return a 403 with a clear message if the limit would be exceeded. `None` means unlimited. Apply the same pattern to any other numeric capabilities added in the future.

---

## 4. No Rate Limiting on WebSocket Connections

**Risk:** A single user can hold many concurrent WebSocket connections, exhausting server resources.

The HTTP API has throttling configured (`apps/utils/throttling.py`), but the WebSocket consumer has no equivalent protection. There is also no limit on how many times a user can reconnect within a time window.

**Fix:** On `connect()` in `NotificationConsumer`, check the number of active connections for this user's group in the channel layer (stored in Redis). Reject connections above a per-user ceiling (e.g. 5 concurrent). Add a connection-rate limit as well (e.g. 10 new connections per minute per user).

---

## From Security Audit (`SECURITY.md` — 2026-03-25)

Open findings from the internal audit that require action before production.

### High

**H3 — Setup script uses `curl | bash`**
`ops/COOLIFY_SETUP.md` line 28 documents a `curl | bash` install pattern. This executes arbitrary remote code without inspection — if the CDN or DNS is compromised, the setup script could be replaced. Verify the script contents locally before piping to bash, or switch to downloading and reviewing it first.

**~~H6 — Known CVE in Next.js (`CVE-2025-66478`)~~** ✓ Fixed — upgraded to 15.5.14

### Medium

**M1 — CORS allows any subdomain of `BASE_DOMAIN`**
`config/settings/base.py` line 270 uses a broad regex that whitelists every subdomain. This is required for multi-tenancy but means any subdomain — including ones that haven't been formally registered — can make credentialed API requests.
**Fix:** Ensure tenant subdomain registration is strictly gated (auth + validation) so no arbitrary subdomain can be claimed and used to exfiltrate data.

**~~M10 — GitHub Actions pinned to tags, not commit SHAs~~** ✓ Fixed — all actions pinned to latest release SHAs (`checkout@v6.0.2`, `setup-node@v6.3.0`, `setup-uv@v7.6.0`, `pnpm/action-setup@v5.0.0`)

### Low

**L4 — No security event logging**
Role changes, email changes, and repeated auth failures leave no audit trail. There is no way to investigate a compromised account after the fact.
**Fix:** Log security-significant events (role change, email change, password change, failed login bursts) to a dedicated log stream or the future audit log (see `ROADMAP.md`). At minimum, use Django's existing `logger` with a structured format and ship logs to Sentry or a log aggregator.

**L5 — No documented database backup strategy**
The deployment docs don't specify backup frequency, retention, or restore procedure. A database loss without a tested backup is unrecoverable.
**Fix:** Configure automated daily Postgres backups (Coolify supports this, or use `pg_dump` via a cron task). Document the restore procedure and test it at least once before launch.

**~~L7 — Deprecated transitive dependency~~** ✓ Fixed — updated `eslint-config-next` to 15.5.14, added pnpm overrides for `esbuild`, `picomatch` (2.x and 4.x paths). `pnpm audit` reports no known vulnerabilities.
