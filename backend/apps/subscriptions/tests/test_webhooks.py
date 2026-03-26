"""
Tests for Stripe webhook handlers.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.webhooks import handle_webhook
from apps.tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@webhook.com", password="pass123")


@pytest.fixture
def tenant(db, owner):
    return Tenant.objects.create(name="WebhookCo", slug="webhookco", owner=owner)


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        name="Pro",
        stripe_price_id="price_test123",
        amount="29.00",
        interval="month",
    )


@pytest.fixture
def subscription(db, tenant, plan):
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan,
        status=Subscription.Status.TRIALING,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123",
    )


def make_event(event_type: str, data: dict) -> dict:
    return {"type": event_type, "data": {"object": data}}


@pytest.mark.django_db
class TestCheckoutCompleted:
    def test_creates_subscription(self, tenant, plan):
        event = make_event(
            "checkout.session.completed",
            {
                "subscription": "sub_new123",
                "customer": "cus_new123",
                "client_reference_id": str(tenant.pk),
            },
        )
        handle_webhook(event)
        sub = Subscription.objects.get(tenant=tenant)
        assert sub.stripe_subscription_id == "sub_new123"
        assert sub.stripe_customer_id == "cus_new123"
        assert sub.status == Subscription.Status.ACTIVE

    def test_skips_missing_reference(self, tenant):
        event = make_event(
            "checkout.session.completed",
            {"subscription": "sub_x", "customer": "cus_x"},
        )
        # Should not raise, just log warning
        handle_webhook(event)

    def test_skips_unknown_tenant(self):
        event = make_event(
            "checkout.session.completed",
            {
                "subscription": "sub_x",
                "customer": "cus_x",
                "client_reference_id": "99999",
            },
        )
        handle_webhook(event)  # Should not raise


@pytest.mark.django_db
class TestInvoicePaid:
    def test_sets_active_and_period(self, subscription):
        now_ts = int(timezone.now().timestamp())
        future_ts = now_ts + 30 * 24 * 3600

        event = make_event(
            "invoice.paid",
            {
                "subscription": "sub_test123",
                "lines": {"data": [{"period": {"start": now_ts, "end": future_ts}}]},
            },
        )
        handle_webhook(event)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.ACTIVE
        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None

    def test_skips_unknown_subscription(self):
        event = make_event("invoice.paid", {"subscription": "sub_unknown"})
        handle_webhook(event)  # Should not raise


@pytest.mark.django_db
class TestSubscriptionUpdated:
    def test_marks_cancelling_when_cancel_at_period_end(self, subscription):
        event = make_event(
            "customer.subscription.updated",
            {
                "id": "sub_test123",
                "status": "active",
                "cancel_at_period_end": True,
                "current_period_start": None,
                "current_period_end": None,
                "trial_end": None,
            },
        )
        handle_webhook(event)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.CANCELLING

    def test_sets_past_due(self, subscription):
        event = make_event(
            "customer.subscription.updated",
            {
                "id": "sub_test123",
                "status": "past_due",
                "cancel_at_period_end": False,
                "current_period_start": None,
                "current_period_end": None,
                "trial_end": None,
            },
        )
        handle_webhook(event)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.PAST_DUE


@pytest.mark.django_db
class TestSubscriptionDeleted:
    def test_marks_cancelled(self, subscription):
        event = make_event(
            "customer.subscription.deleted",
            {"id": "sub_test123"},
        )
        handle_webhook(event)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.CANCELLED
        assert subscription.cancelled_at is not None
