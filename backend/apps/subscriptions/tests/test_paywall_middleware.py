"""
Tests for SubscriptionPaywallMiddleware.
"""

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from apps.subscriptions.middleware import SubscriptionPaywallMiddleware


def get_response(request):
    return HttpResponse("ok", status=200)


def make_request(path="/api/v1/dashboard/", auth=True):
    factory = RequestFactory()
    req = factory.get(path)
    req.tenant = None  # set per test
    if auth:
        req.META["HTTP_AUTHORIZATION"] = "Bearer fake-token"
    return req


@pytest.mark.django_db
class TestPaywallMiddleware:
    def test_feature_disabled_passes_all_requests(self):
        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": False}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            resp = mw(req)
            assert resp.status_code == 200

    def test_no_tenant_passes(self):
        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            req.tenant = None
            resp = mw(req)
            assert resp.status_code == 200

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/auth/login/",
            "/api/v1/auth/register/",
            "/api/v1/features/",
            "/api/v1/subscriptions/plans/",
            "/api/v1/support/",
            "/api/docs/",
            "/health",
        ],
    )
    def test_exempt_paths_pass(self, path):
        from apps.tenants.models import Tenant

        tenant = Tenant(name="T", slug="t")

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request(path=path)
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 200, f"Expected pass for {path}"

    def test_unauthenticated_request_passes(self):
        from apps.tenants.models import Tenant

        tenant = Tenant(name="T", slug="t")

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request(auth=False)
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 200

    def test_no_subscription_returns_402(self):
        from apps.tenants.models import Tenant
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(email="pay@test.com", password="x")
        tenant = Tenant.objects.create(name="NoPay", slug="no-pay", owner=user)

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 402

    def test_active_subscription_passes(self):
        from apps.subscriptions.models import Plan, Subscription
        from apps.tenants.models import Tenant
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(email="active@test.com", password="x")
        tenant = Tenant.objects.create(name="Active Co", slug="active-co", owner=user)
        plan = Plan.objects.create(
            name="Starter",
            amount=900,
            stripe_price_id="price_x",
            stripe_product_id="prod_x",
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_x",
            stripe_customer_id="cus_x",
        )

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 200

    def test_trialing_subscription_passes(self):
        from apps.subscriptions.models import Plan, Subscription
        from apps.tenants.models import Tenant
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(email="trial@test.com", password="x")
        tenant = Tenant.objects.create(name="Trial Co", slug="trial-co", owner=user)
        plan = Plan.objects.create(
            name="Pro",
            amount=2900,
            stripe_price_id="price_y",
            stripe_product_id="prod_y",
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.TRIALING,
            stripe_subscription_id="sub_y",
            stripe_customer_id="cus_y",
        )

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 200

    def test_cancelled_subscription_returns_402(self):
        from apps.subscriptions.models import Plan, Subscription
        from apps.tenants.models import Tenant
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(email="cancelled@test.com", password="x")
        tenant = Tenant.objects.create(
            name="Cancelled Co", slug="cancelled-co", owner=user
        )
        plan = Plan.objects.create(
            name="Old",
            amount=900,
            stripe_price_id="price_z",
            stripe_product_id="prod_z",
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.CANCELLED,
            stripe_subscription_id="sub_z",
            stripe_customer_id="cus_z",
        )

        with override_settings(FEATURE_FLAGS={"REQUIRE_SUBSCRIPTION": True}):
            mw = SubscriptionPaywallMiddleware(get_response)
            req = make_request()
            req.tenant = tenant
            resp = mw(req)
            assert resp.status_code == 402
