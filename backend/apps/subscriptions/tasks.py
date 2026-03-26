"""
Celery tasks for subscriptions.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_trial_ending_email(self, subscription_id: int) -> None:
    """Warn the tenant owner that their trial ends in 3 days."""
    from apps.subscriptions.models import Subscription
    from utils.email import send_email

    try:
        subscription = Subscription.objects.select_related("tenant__owner", "plan").get(
            pk=subscription_id
        )
    except Subscription.DoesNotExist:
        logger.error("Subscription %s not found", subscription_id)
        return

    if not subscription.trial_end:
        return

    days_left = (subscription.trial_end - timezone.now()).days
    if days_left > 3:
        return  # Not close enough yet

    owner = subscription.tenant.owner
    app_name = settings.APP_NAME
    plan_name = subscription.plan.name if subscription.plan else "your plan"
    billing_url = f"https://{settings.BASE_DOMAIN}/billing/"

    context = {
        "user": owner,
        "app_name": app_name,
        "plan_name": plan_name,
        "days_left": days_left,
        "billing_url": billing_url,
    }

    subject = f"Your {app_name} trial ends in {days_left} day(s)"
    html_body = render_to_string("subscriptions/email/trial_ending.html", context)
    text_body = render_to_string("subscriptions/email/trial_ending.txt", context)

    try:
        send_email(
            to=owner.email, subject=subject, html_body=html_body, text_body=text_body
        )
        logger.info(
            "Trial ending email sent to %s for subscription %s",
            owner.email,
            subscription_id,
        )
    except Exception as exc:
        logger.warning("Failed to send trial ending email: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_payment_failed_email(self, subscription_id: int, amount: str = "") -> None:
    """Notify the tenant owner that a payment failed (dunning)."""
    from apps.subscriptions.models import Subscription
    from utils.email import send_email

    try:
        subscription = Subscription.objects.select_related("tenant__owner", "plan").get(
            pk=subscription_id
        )
    except Subscription.DoesNotExist:
        logger.error("Subscription %s not found", subscription_id)
        return

    owner = subscription.tenant.owner
    app_name = settings.APP_NAME
    billing_url = f"https://{settings.BASE_DOMAIN}/billing/"

    context = {
        "user": owner,
        "app_name": app_name,
        "amount": amount,
        "billing_url": billing_url,
    }

    subject = f"Payment failed for your {app_name} subscription"
    html_body = render_to_string("subscriptions/email/payment_failed.html", context)
    text_body = render_to_string("subscriptions/email/payment_failed.txt", context)

    try:
        send_email(
            to=owner.email, subject=subject, html_body=html_body, text_body=text_body
        )
        logger.info(
            "Payment failed email sent to %s for subscription %s",
            owner.email,
            subscription_id,
        )
    except Exception as exc:
        logger.warning("Failed to send payment failed email: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_stripe_customer_email(self, user_id: int, new_email: str) -> None:
    """Update Stripe customer email for all tenants owned by this user."""
    import stripe

    from apps.subscriptions.models import Subscription

    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer_ids = list(
        Subscription.objects.filter(
            tenant__owner_id=user_id,
        )
        .exclude(stripe_customer_id="")
        .values_list("stripe_customer_id", flat=True)
    )

    for customer_id in customer_ids:
        try:
            stripe.Customer.modify(customer_id, email=new_email)
            logger.info(
                "Updated Stripe customer %s email to %s", customer_id, new_email
            )
        except stripe.StripeError as exc:
            logger.warning(
                "Failed to update Stripe customer %s email: %s", customer_id, exc
            )
            raise self.retry(exc=exc)


@shared_task
def cleanup_old_webhook_events(days: int = 90) -> None:
    """Delete processed Stripe webhook event records older than `days` to prevent table bloat."""
    from apps.subscriptions.models import StripeWebhookEvent

    cutoff = timezone.now() - timedelta(days=days)
    count, _ = StripeWebhookEvent.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Deleted %d webhook events older than %d days", count, days)


@shared_task
def check_trial_endings() -> None:
    """Find subscriptions with trials ending in <= 3 days and dispatch warning emails."""
    from apps.subscriptions.models import Subscription

    now = timezone.now()
    deadline = now + timedelta(days=3)

    subscriptions = Subscription.objects.filter(
        status=Subscription.Status.TRIALING,
        trial_end__isnull=False,
        trial_end__lte=deadline,
        trial_end__gte=now,
    ).values_list("pk", flat=True)

    count = 0
    for sub_id in subscriptions:
        send_trial_ending_email.delay(sub_id)
        count += 1

    logger.info("Dispatched trial-ending emails for %d subscriptions", count)
