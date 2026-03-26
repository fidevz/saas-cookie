"""
Tests for registration flow: slug selection, company name, tenant creation.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.tenants.models import Tenant

VALID_PAYLOAD = {
    "company_name": "Acme Inc",
    "slug": "acme",
    "email": "founder@acme.com",
    "password": "TestPass123!",
    "first_name": "Jane",
    "last_name": "Doe",
}


@pytest.mark.django_db
class TestCheckSlug:
    def test_available_slug(self):
        client = APIClient()
        resp = client.get(reverse("check-slug"), {"slug": "my-startup"})
        assert resp.status_code == 200
        assert resp.data["available"] is True

    def test_taken_slug_returns_suggestion(self):
        from apps.users.models import CustomUser

        owner = CustomUser.objects.create_user(email="owner@taken.com", password="x")
        Tenant.objects.create(name="Taken", slug="taken", owner=owner)
        client = APIClient()
        resp = client.get(reverse("check-slug"), {"slug": "taken"})
        assert resp.status_code == 200
        assert resp.data["available"] is False
        assert "suggestion" in resp.data
        assert resp.data["suggestion"] == "taken-1"

    def test_reserved_slug(self):
        client = APIClient()
        resp = client.get(reverse("check-slug"), {"slug": "admin"})
        assert resp.status_code == 200
        assert resp.data["available"] is False

    def test_invalid_format_slug(self):
        client = APIClient()
        resp = client.get(reverse("check-slug"), {"slug": "-bad-slug-"})
        assert resp.status_code == 200
        assert resp.data["available"] is False
        assert "error" in resp.data

    def test_missing_slug_param(self):
        client = APIClient()
        resp = client.get(reverse("check-slug"))
        assert resp.status_code == 400


@pytest.mark.django_db
class TestRegisterView:
    def test_register_creates_tenant_with_chosen_slug(self):
        client = APIClient()
        resp = client.post(reverse("auth-register"), VALID_PAYLOAD, format="json")
        assert resp.status_code == 201
        assert Tenant.objects.filter(slug="acme").exists()

    def test_register_uses_company_name(self):
        client = APIClient()
        client.post(reverse("auth-register"), VALID_PAYLOAD, format="json")
        tenant = Tenant.objects.get(slug="acme")
        assert tenant.name == "Acme Inc"

    def test_register_response_includes_tenant_slug(self):
        client = APIClient()
        resp = client.post(reverse("auth-register"), VALID_PAYLOAD, format="json")
        assert resp.status_code == 201
        assert resp.data["tenant_slug"] == "acme"

    def test_register_response_includes_exchange_code(self):
        client = APIClient()
        resp = client.post(reverse("auth-register"), VALID_PAYLOAD, format="json")
        assert "code" in resp.data

    def test_register_duplicate_slug_returns_400(self):
        client = APIClient()
        client.post(reverse("auth-register"), VALID_PAYLOAD, format="json")
        payload2 = {**VALID_PAYLOAD, "email": "other@acme.com"}
        resp = client.post(reverse("auth-register"), payload2, format="json")
        assert resp.status_code == 400
        assert "slug" in str(resp.data).lower() or "taken" in str(resp.data).lower()

    def test_register_reserved_slug_returns_400(self):
        payload = {**VALID_PAYLOAD, "slug": "admin"}
        client = APIClient()
        resp = client.post(reverse("auth-register"), payload, format="json")
        assert resp.status_code == 400

    def test_register_missing_company_name_returns_400(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "company_name"}
        client = APIClient()
        resp = client.post(reverse("auth-register"), payload, format="json")
        assert resp.status_code == 400

    def test_register_missing_slug_returns_400(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "slug"}
        client = APIClient()
        resp = client.post(reverse("auth-register"), payload, format="json")
        assert resp.status_code == 400

    def test_register_short_slug_returns_400(self):
        payload = {**VALID_PAYLOAD, "slug": "ab"}
        client = APIClient()
        resp = client.post(reverse("auth-register"), payload, format="json")
        assert resp.status_code == 400

    def test_register_slug_with_uppercase_returns_400(self):
        payload = {**VALID_PAYLOAD, "slug": "Acme"}
        client = APIClient()
        resp = client.post(reverse("auth-register"), payload, format="json")
        assert resp.status_code == 400
