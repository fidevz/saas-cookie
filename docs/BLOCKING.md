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
