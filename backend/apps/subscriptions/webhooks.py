"""
Stripe webhook event handlers.
"""

import logging
from datetime import UTC, datetime

from django.utils import timezone as django_timezone

from utils.audit import log_action

logger = logging.getLogger(__name__)


def _dt(ts) -> datetime | None:
    """Convert a Stripe Unix timestamp to a timezone-aware datetime."""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=UTC)


def handle_webhook(event: dict) -> None:
    """Dispatch a Stripe webhook event to the appropriate handler."""
    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    handlers = {
        "checkout.session.completed": _handle_checkout_completed,
        "invoice.paid": _handle_invoice_paid,
        "invoice.payment_failed": _handle_invoice_payment_failed,
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
    import stripe
    from django.conf import settings

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

    plan = None
    plan_id = session.get("metadata", {}).get("plan_id")
    if plan_id:
        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            logger.warning("checkout.session.completed: plan %s not found", plan_id)

    # Fetch period dates from the Stripe subscription object
    period_start = period_end = trial_end = None
    if stripe_subscription_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            # Period dates live on the first item in newer Stripe API versions
            items = stripe_sub.get("items", {}).get("data", [])
            if items:
                period_start = _dt(items[0].get("current_period_start"))
                period_end = _dt(items[0].get("current_period_end"))
            trial_end = _dt(stripe_sub.get("trial_end"))
        except Exception as exc:
            logger.warning("Could not retrieve Stripe subscription dates: %s", exc)

    subscription, _ = Subscription.objects.get_or_create(tenant=tenant)
    subscription.stripe_subscription_id = stripe_subscription_id or ""
    subscription.stripe_customer_id = stripe_customer_id or ""
    subscription.status = Subscription.Status.ACTIVE
    if plan:
        subscription.plan = plan
        subscription.capabilities = plan.capabilities  # snapshot at subscription time
    if period_start:
        subscription.current_period_start = period_start
    if period_end:
        subscription.current_period_end = period_end
    if trial_end:
        subscription.trial_end = trial_end
    subscription.save(
        update_fields=[
            "stripe_subscription_id",
            "stripe_customer_id",
            "status",
            "plan",
            "capabilities",
            "current_period_start",
            "current_period_end",
            "trial_end",
            "updated_at",
        ]
    )
    logger.info("Checkout completed for tenant %s", tenant.slug)
    log_action(
        actor=None,
        action="subscription.acquired",
        target=tenant.slug,
        metadata={
            "source": "stripe_webhook",
            "plan_id": str(plan.pk) if plan else None,
            "stripe_subscription_id": stripe_subscription_id,
        },
        tenant=tenant,
    )


def _handle_invoice_paid(invoice: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = invoice.get("subscription")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription_id
        )
    except Subscription.DoesNotExist:
        logger.warning(
            "invoice.paid: subscription %s not found", stripe_subscription_id
        )
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
        update_fields=[
            "status",
            "current_period_start",
            "current_period_end",
            "updated_at",
        ]
    )
    logger.info("Invoice paid for subscription %s", stripe_subscription_id)
    log_action(
        actor=None,
        action="subscription.payment_succeeded",
        target=stripe_subscription_id,
        metadata={"source": "stripe_webhook"},
        tenant=subscription.tenant,
    )


def _handle_invoice_payment_failed(invoice: dict) -> None:
    from apps.subscriptions.models import Subscription
    from apps.subscriptions.tasks import send_payment_failed_email

    stripe_subscription_id = invoice.get("subscription")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription_id
        )
    except Subscription.DoesNotExist:
        logger.warning(
            "invoice.payment_failed: subscription %s not found", stripe_subscription_id
        )
        return

    # Format amount from Stripe's integer cents
    amount_due = invoice.get("amount_due", 0)
    currency = invoice.get("currency", "usd").upper()
    amount_str = f"{currency} {amount_due / 100:.2f}" if amount_due else ""

    subscription.status = Subscription.Status.PAST_DUE
    subscription.save(update_fields=["status", "updated_at"])
    logger.info("Payment failed for subscription %s", stripe_subscription_id)
    log_action(
        actor=None,
        action="subscription.payment_failed",
        target=stripe_subscription_id,
        metadata={"source": "stripe_webhook", "amount": amount_str},
        tenant=subscription.tenant,
    )

    # Dispatch dunning email asynchronously
    send_payment_failed_email.delay(subscription.pk, amount=amount_str)


def _handle_subscription_updated(stripe_sub: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = stripe_sub.get("id")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.select_related("tenant").get(
            stripe_subscription_id=stripe_subscription_id
        )
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
    logger.info(
        "Subscription %s updated: status=%s", stripe_subscription_id, new_status
    )
    log_action(
        actor=None,
        action="subscription.upgraded",
        target=stripe_subscription_id,
        metadata={"source": "stripe_webhook", "new_status": new_status},
        tenant=subscription.tenant,
    )


def _handle_subscription_deleted(stripe_sub: dict) -> None:
    from apps.subscriptions.models import Subscription

    stripe_subscription_id = stripe_sub.get("id")
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.select_related("tenant").get(
            stripe_subscription_id=stripe_subscription_id
        )
    except Subscription.DoesNotExist:
        logger.warning("subscription.deleted: %s not found", stripe_subscription_id)
        return

    subscription.status = Subscription.Status.CANCELLED
    subscription.cancelled_at = django_timezone.now()
    subscription.save(update_fields=["status", "cancelled_at", "updated_at"])
    logger.info("Subscription %s cancelled", stripe_subscription_id)
    log_action(
        actor=None,
        action="subscription.cancelled",
        target=stripe_subscription_id,
        metadata={"source": "stripe_webhook"},
        tenant=subscription.tenant,
    )
