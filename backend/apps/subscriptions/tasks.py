"""
Celery tasks for subscriptions.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_trial_ending_email(self, subscription_id: int) -> None:
    """Warn the tenant owner that their trial ends in 3 days."""
    from apps.subscriptions.models import Subscription
    from utils.email import send_email

    try:
        subscription = Subscription.objects.select_related(
            "tenant__owner", "plan"
        ).get(pk=subscription_id)
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

    subject = f"Your {app_name} trial ends in {days_left} day(s)"
    html_body = f"""
    <h2>Your trial is ending soon</h2>
    <p>Hi {owner.first_name or owner.email},</p>
    <p>Your free trial of <strong>{plan_name}</strong> on {app_name} ends in
    <strong>{days_left} day(s)</strong>.</p>
    <p>To keep access, please add a payment method:</p>
    <p>
        <a href="{billing_url}" style="
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
        ">Manage Billing</a>
    </p>
    <p>Questions? Reply to this email — we're happy to help.</p>
    """

    try:
        send_email(to=owner.email, subject=subject, html_body=html_body)
        logger.info(
            "Trial ending email sent to %s for subscription %s",
            owner.email,
            subscription_id,
        )
    except Exception as exc:
        logger.warning("Failed to send trial ending email: %s", exc)
        raise self.retry(exc=exc)


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
