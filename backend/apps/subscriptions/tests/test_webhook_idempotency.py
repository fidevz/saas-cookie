"""
Tests for Stripe webhook idempotency (event deduplication).
"""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.subscriptions.models import Plan, StripeWebhookEvent, Subscription
from apps.subscriptions.tasks import cleanup_old_webhook_events
from apps.tenants.models import Tenant

User = get_user_model()

WEBHOOK_URL = "/api/v1/subscriptions/webhook/"


def make_stripe_event(event_id: str, event_type: str, data: dict) -> dict:
    return {"id": event_id, "type": event_type, "data": {"object": data}}


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@idempotency.com", password="pass123")


@pytest.fixture
def tenant(db, owner):
    return Tenant.objects.create(name="IdempCo", slug="idempco", owner=owner)


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        name="Pro",
        stripe_price_id="price_idemp123",
        amount="29.00",
        interval="month",
    )


@pytest.fixture
def subscription(db, tenant, plan):
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan,
        status=Subscription.Status.ACTIVE,
        stripe_subscription_id="sub_idemp123",
        stripe_customer_id="cus_idemp123",
    )


def post_webhook(client, payload):
    """Post a webhook, bypassing Stripe signature verification."""
    with patch(
        "apps.subscriptions.views.stripe.Webhook.construct_event"
    ) as mock_construct:
        mock_construct.return_value = payload
        return client.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=fake",
        )


@pytest.mark.django_db
class TestWebhookIdempotency:
    def setup_method(self):
        self.client = APIClient()

    def test_first_delivery_is_processed(self, subscription):
        event = make_stripe_event(
            "evt_001",
            "invoice.payment_failed",
            {"subscription": "sub_idemp123", "amount_due": 2900, "currency": "usd"},
        )
        with patch("apps.subscriptions.tasks.send_payment_failed_email") as mock_task:
            response = post_webhook(self.client, event)

        assert response.status_code == status.HTTP_200_OK
        assert StripeWebhookEvent.objects.filter(event_id="evt_001").count() == 1
        mock_task.delay.assert_called_once()

    def test_duplicate_delivery_is_skipped(self, subscription):
        event = make_stripe_event(
            "evt_002",
            "invoice.payment_failed",
            {"subscription": "sub_idemp123", "amount_due": 2900, "currency": "usd"},
        )
        with patch("apps.subscriptions.tasks.send_payment_failed_email") as mock_task:
            r1 = post_webhook(self.client, event)
            r2 = post_webhook(self.client, event)

        assert r1.status_code == status.HTTP_200_OK
        assert r2.status_code == status.HTTP_200_OK
        # Only one record stored
        assert StripeWebhookEvent.objects.filter(event_id="evt_002").count() == 1
        # Email dispatched only once
        mock_task.delay.assert_called_once()

    def test_different_event_ids_both_processed(self, subscription):
        event_a = make_stripe_event(
            "evt_003a",
            "invoice.payment_failed",
            {"subscription": "sub_idemp123", "amount_due": 2900, "currency": "usd"},
        )
        event_b = make_stripe_event(
            "evt_003b",
            "invoice.payment_failed",
            {"subscription": "sub_idemp123", "amount_due": 2900, "currency": "usd"},
        )
        with patch("apps.subscriptions.tasks.send_payment_failed_email") as mock_task:
            post_webhook(self.client, event_a)
            post_webhook(self.client, event_b)

        assert (
            StripeWebhookEvent.objects.filter(
                event_id__in=["evt_003a", "evt_003b"]
            ).count()
            == 2
        )
        assert mock_task.delay.call_count == 2

    def test_dedup_record_stores_event_type(self, subscription):
        event = make_stripe_event(
            "evt_004",
            "customer.subscription.updated",
            {
                "id": "sub_idemp123",
                "status": "active",
                "cancel_at_period_end": False,
                "current_period_start": None,
                "current_period_end": None,
                "trial_end": None,
            },
        )
        post_webhook(self.client, event)
        record = StripeWebhookEvent.objects.get(event_id="evt_004")
        assert record.event_type == "customer.subscription.updated"


@pytest.mark.django_db
class TestCleanupOldWebhookEvents:
    def test_deletes_old_events(self):
        old = StripeWebhookEvent.objects.create(
            event_id="evt_old", event_type="invoice.paid"
        )
        # Backdate created_at by 91 days
        StripeWebhookEvent.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=91)
        )
        recent = StripeWebhookEvent.objects.create(
            event_id="evt_recent", event_type="invoice.paid"
        )

        cleanup_old_webhook_events(days=90)

        assert not StripeWebhookEvent.objects.filter(pk=old.pk).exists()
        assert StripeWebhookEvent.objects.filter(pk=recent.pk).exists()
