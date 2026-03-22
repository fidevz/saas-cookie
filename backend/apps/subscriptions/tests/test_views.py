"""
Tests for subscription views.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.subscriptions.models import Plan, Subscription
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()

FEATURES_ON = {"FEATURE_FLAGS": {"TEAMS": True, "BILLING": True, "NOTIFICATIONS": True}}


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@subs.com", password="pass123")


@pytest.fixture
def tenant(db, owner):
    t = Tenant.objects.create(name="SubCo", slug="subco", owner=owner)
    TenantMembership.objects.create(user=owner, tenant=t, role="admin")
    return t


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        name="Starter",
        stripe_price_id="price_starter",
        amount="9.00",
        interval="month",
        is_active=True,
    )


@pytest.fixture
def subscription(db, tenant, plan):
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan,
        status=Subscription.Status.ACTIVE,
        stripe_subscription_id="sub_test",
        stripe_customer_id="cus_test",
    )


@pytest.mark.django_db
class TestListPlansView:
    url = "/api/v1/subscriptions/plans/"

    def test_public_returns_active_plans(self, plan):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert any(p["stripe_price_id"] == "price_starter" for p in response.data)

    def test_inactive_plans_excluded(self, plan):
        plan.is_active = False
        plan.save()
        response = APIClient().get(self.url)
        assert not any(p["stripe_price_id"] == "price_starter" for p in response.data)


@pytest.mark.django_db
class TestWebhookView:
    url = "/api/v1/subscriptions/webhook/"

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_webhook_no_secret_processes_event(self, tenant):
        payload = json.dumps(
            {
                "type": "customer.subscription.deleted",
                "data": {"object": {"id": "sub_nonexistent"}},
            }
        ).encode()
        response = APIClient().post(
            self.url, data=payload, content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_webhook_invalid_signature_returns_400(self):
        payload = b'{"type": "test"}'
        response = APIClient().post(
            self.url,
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCancelSubscriptionView:
    url = "/api/v1/subscriptions/cancel/"

    @override_settings(**FEATURES_ON)
    @patch("apps.subscriptions.views.stripe.Subscription.modify")
    def test_cancel_without_tenant_context(self, mock_modify, owner, tenant, subscription):
        """Without tenant middleware, IsTenantAdmin returns 403."""
        client = auth_client(owner)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_modify.assert_not_called()

    def test_unauthenticated_returns_401(self):
        response = APIClient().post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
