"""
Tests for TenantMiddleware subdomain extraction.
"""

import pytest
from django.test import RequestFactory, override_settings

from apps.tenants.middleware import TenantMiddleware


@pytest.fixture
def factory():
    return RequestFactory()


def make_middleware():
    def dummy_response(request):
        return None

    return TenantMiddleware(dummy_response)


class TestSlugExtraction:
    """Unit tests for _extract_slug — no DB needed."""

    def test_returns_none_for_root_domain(self):
        assert (
            TenantMiddleware._extract_slug("yourdomain.com", "yourdomain.com") is None
        )

    def test_extracts_subdomain(self):
        assert (
            TenantMiddleware._extract_slug("acme.yourdomain.com", "yourdomain.com")
            == "acme"
        )

    def test_returns_none_for_www(self):
        assert (
            TenantMiddleware._extract_slug("www.yourdomain.com", "yourdomain.com")
            is None
        )

    def test_returns_none_for_api(self):
        assert (
            TenantMiddleware._extract_slug("api.yourdomain.com", "yourdomain.com")
            is None
        )

    def test_localhost_subdomain(self):
        assert TenantMiddleware._extract_slug("acme.localhost", "localhost") == "acme"

    def test_localhost_root(self):
        assert TenantMiddleware._extract_slug("localhost", "localhost") is None

    def test_unrelated_host_returns_none(self):
        assert TenantMiddleware._extract_slug("evil.com", "yourdomain.com") is None


@pytest.mark.django_db
class TestMiddlewareIntegration:
    @override_settings(BASE_DOMAIN="yourdomain.com")
    def test_sets_tenant_on_request(self, factory):
        from apps.tenants.models import Tenant
        from apps.users.models import CustomUser

        owner = CustomUser.objects.create_user(email="owner@test.com", password="pass")
        tenant = Tenant.objects.create(name="Acme", slug="acme", owner=owner)

        middleware = make_middleware()
        request = factory.get("/api/v1/features/", HTTP_HOST="acme.yourdomain.com")
        middleware(request)
        assert request.tenant == tenant

    @override_settings(BASE_DOMAIN="yourdomain.com")
    def test_sets_none_for_root_domain(self, factory):
        middleware = make_middleware()
        request = factory.get("/api/v1/features/", HTTP_HOST="yourdomain.com")
        middleware(request)
        assert request.tenant is None

    @override_settings(BASE_DOMAIN="yourdomain.com")
    def test_sets_none_for_unknown_subdomain(self, factory):
        middleware = make_middleware()
        request = factory.get("/api/v1/features/", HTTP_HOST="unknown.yourdomain.com")
        middleware(request)
        assert request.tenant is None

    @override_settings(BASE_DOMAIN="yourdomain.com", ADMIN_URL="tacomate")
    def test_skips_admin_path(self, factory):
        middleware = make_middleware()
        request = factory.get("/tacomate/", HTTP_HOST="acme.yourdomain.com")
        middleware(request)
        assert request.tenant is None
