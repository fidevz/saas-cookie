"""
Tests for subscription Celery tasks.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.tasks import sync_stripe_customer_email
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@example.com", password="pw")


@pytest.fixture
def plan(db):
    return Plan.objects.create(name="Pro", stripe_price_id="price_pro", amount=1000, currency="usd")


@pytest.fixture
def tenant(owner):
    t = Tenant.objects.create(name="Acme", slug="acme", owner=owner)
    TenantMembership.objects.create(user=owner, tenant=t, role=TenantMembership.Role.ADMIN)
    return t


@pytest.fixture
def subscription(tenant, plan):
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan,
        stripe_customer_id="cus_abc123",
    )


@pytest.mark.django_db
class TestSyncStripeCustomerEmail:
    @patch("stripe.Customer.modify")
    def test_updates_stripe_customer_for_owned_tenant(self, mock_modify, subscription, owner):
        sync_stripe_customer_email(owner.pk, "new@example.com")
        mock_modify.assert_called_once_with("cus_abc123", email="new@example.com")

    @patch("stripe.Customer.modify")
    def test_skips_subscription_without_stripe_customer_id(self, mock_modify, owner, tenant, plan):
        Subscription.objects.create(tenant=tenant, plan=plan, stripe_customer_id="")
        sync_stripe_customer_email(owner.pk, "new@example.com")
        mock_modify.assert_not_called()

    @patch("stripe.Customer.modify")
    def test_updates_all_owned_tenants(self, mock_modify, owner, plan, db):
        t1 = Tenant.objects.create(name="A", slug="ta", owner=owner)
        t2 = Tenant.objects.create(name="B", slug="tb", owner=owner)
        Subscription.objects.create(tenant=t1, plan=plan, stripe_customer_id="cus_111")
        Subscription.objects.create(tenant=t2, plan=plan, stripe_customer_id="cus_222")

        sync_stripe_customer_email(owner.pk, "new@example.com")

        called_with = {c.args[0] for c in mock_modify.call_args_list}
        assert called_with == {"cus_111", "cus_222"}
        for c in mock_modify.call_args_list:
            assert c.kwargs == {"email": "new@example.com"}

    @patch("stripe.Customer.modify")
    def test_does_nothing_when_user_owns_no_tenants(self, mock_modify, owner):
        sync_stripe_customer_email(owner.pk, "new@example.com")
        mock_modify.assert_not_called()

    @patch("stripe.Customer.modify")
    def test_does_nothing_for_nonexistent_user(self, mock_modify, db):
        sync_stripe_customer_email(99999, "new@example.com")
        mock_modify.assert_not_called()

    @patch("stripe.Customer.modify")
    def test_stripe_error_triggers_retry(self, mock_modify, subscription, owner):
        import stripe as stripe_lib

        mock_modify.side_effect = stripe_lib.StripeError("network error")
        # self.retry(exc=exc) re-raises the original exception in the test context
        with pytest.raises(stripe_lib.StripeError):
            sync_stripe_customer_email(owner.pk, "new@example.com")
