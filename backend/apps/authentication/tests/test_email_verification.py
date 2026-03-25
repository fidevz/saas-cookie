"""
Tests for email verification enforcement in LoginView and ResendVerificationView.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import CustomUser


def make_verified_user(email="verified@test.com", password="TestPass123!"):
    from allauth.account.models import EmailAddress

    user = CustomUser.objects.create_user(email=email, password=password)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


def make_unverified_user(email="unverified@test.com", password="TestPass123!"):
    from allauth.account.models import EmailAddress

    user = CustomUser.objects.create_user(email=email, password=password)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=False)
    return user


@pytest.mark.django_db
class TestLoginEmailVerification:
    def test_login_unverified_returns_403(self):
        make_unverified_user()
        client = APIClient()
        resp = client.post(
            reverse("auth-login"),
            {"email": "unverified@test.com", "password": "TestPass123!"},
            format="json",
        )
        assert resp.status_code == 403
        assert resp.data["code"] == "email_not_verified"

    def test_login_verified_returns_200_with_tokens(self):
        make_verified_user()
        client = APIClient()
        resp = client.post(
            reverse("auth-login"),
            {"email": "verified@test.com", "password": "TestPass123!"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_login_verified_response_includes_tenant_slug(self):
        from apps.tenants.models import Tenant, TenantMembership

        user = make_verified_user(email="tenant-user@test.com")
        tenant = Tenant.objects.create(name="My Co", slug="my-co", owner=user)
        TenantMembership.objects.create(
            user=user, tenant=tenant, role=TenantMembership.Role.ADMIN
        )
        client = APIClient()
        resp = client.post(
            reverse("auth-login"),
            {"email": "tenant-user@test.com", "password": "TestPass123!"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["tenant_slug"] == "my-co"

    def test_login_wrong_password_returns_400(self):
        make_verified_user()
        client = APIClient()
        resp = client.post(
            reverse("auth-login"),
            {"email": "verified@test.com", "password": "WrongPass!"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestResendVerification:
    def test_resend_always_returns_200(self):
        client = APIClient()
        resp = client.post(
            reverse("resend-verification"),
            {"email": "nonexistent@test.com"},
            format="json",
        )
        assert resp.status_code == 200
        assert "detail" in resp.data

    def test_resend_for_unverified_sends_email(self, mailoutbox):
        make_unverified_user(email="sendme@test.com")
        client = APIClient()
        resp = client.post(
            reverse("resend-verification"),
            {"email": "sendme@test.com"},
            format="json",
        )
        assert resp.status_code == 200
        assert len(mailoutbox) >= 1

    def test_resend_for_verified_does_not_send(self, mailoutbox):
        make_verified_user(email="already-verified@test.com")
        client = APIClient()
        resp = client.post(
            reverse("resend-verification"),
            {"email": "already-verified@test.com"},
            format="json",
        )
        assert resp.status_code == 200
        assert len(mailoutbox) == 0
