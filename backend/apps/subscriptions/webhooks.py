"""
Stripe webhook event handlers.
"""
import logging
from datetime import datetime, timezone

from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


def _dt(ts) -> datetime | None:
    """Convert a Stripe Unix timestamp to a timezone-aware datetime."""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def handle_webhook(event: dict) -> None:
    """Dispatch a Stripe webhook event to the appropriate handler."""
    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    handlers = {
        "checkout.session.completed": _handle_checkout_completed,
        "invoice.paid": _handle_invoice_paid,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            handler(data_object)
        except Exception as exc:
            logger.exception("Error handling Stripe event %s: %s", event_type, exc)
            raise
    else:
        logger.debug("Unhandled Stripe event: %s", event_type)


def _handle_checkout_completed(session: dict) -> None:
    from apps.subscriptions.models import Plan, Subscription
    from apps.tenants.models import Tenant

    stripe_subscription_id = session.get("subscription")
    stripe_customer_id = session.get("customer")
    client_reference_id = session.get("client_reference_id")  # tenant pk

    if not client_reference_id:
        logger.warning("checkout.session.completed: missing client_reference_id")
        return

    try:
        tenant = Tenant.objects.get(pk=client_reference_id)
    except Tenant.DoesNotExist:
        logger.error("Tenant %s not found for checkout session", client_reference_id)
        return

    subscription, _ = Subscription.objects.get_or_create(tenant=tenant)
    subscription.stripe_subscription_id = stripe_subscription_id or ""
    subscription.stripe_customer_id = stripe_customer_id or ""
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(
        update_fields=["stripe_subscription_id", "stripe_customer_id", "status", "updated_at"]
    )
    logger.info("Checkout completed for tenant %s", tenant.slug)


def _handle_invoice_paid(invoice: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = invoice.get("subscription")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("invoice.paid: subscription %s not found", stripe_subscription_id)
        return

    lines = invoice.get("lines", {}).get("data", [])
    period_start = period_end = None
    for line in lines:
        period_start = _dt(line.get("period", {}).get("start"))
        period_end = _dt(line.get("period", {}).get("end"))
        break

    subscription.status = Subscription.Status.ACTIVE
    subscription.current_period_start = period_start
    subscription.current_period_end = period_end
    subscription.save(
        update_fields=["status", "current_period_start", "current_period_end", "updated_at"]
    )
    logger.info("Invoice paid for subscription %s", stripe_subscription_id)


def _handle_subscription_updated(stripe_sub: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = stripe_sub.get("id")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("subscription.updated: %s not found", stripe_subscription_id)
        return

    stripe_status = stripe_sub.get("status", "")
    cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)

    status_map = {
        "trialing": Subscription.Status.TRIALING,
        "active": Subscription.Status.ACTIVE,
        "past_due": Subscription.Status.PAST_DUE,
        "unpaid": Subscription.Status.UNPAID,
        "canceled": Subscription.Status.CANCELLED,
        "incomplete": Subscription.Status.PAST_DUE,
        "incomplete_expired": Subscription.Status.CANCELLED,
    }

    new_status = status_map.get(stripe_status, Subscription.Status.PAST_DUE)
    if cancel_at_period_end and new_status == Subscription.Status.ACTIVE:
        new_status = Subscription.Status.CANCELLING

    subscription.status = new_status
    subscription.current_period_start = _dt(stripe_sub.get("current_period_start"))
    subscription.current_period_end = _dt(stripe_sub.get("current_period_end"))
    subscription.trial_end = _dt(stripe_sub.get("trial_end"))
    subscription.save(
        update_fields=[
            "status",
            "current_period_start",
            "current_period_end",
            "trial_end",
            "updated_at",
        ]
    )
    logger.info("Subscription %s updated: status=%s", stripe_subscription_id, new_status)


def _handle_subscription_deleted(stripe_sub: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = stripe_sub.get("id")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("subscription.deleted: %s not found", stripe_subscription_id)
        return

    subscription.status = Subscription.Status.CANCELLED
    subscription.cancelled_at = django_timezone.now()
    subscription.save(update_fields=["status", "cancelled_at", "updated_at"])
    logger.info("Subscription %s cancelled", stripe_subscription_id)
