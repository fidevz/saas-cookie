"""
Integration tests for authentication endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def existing_user(db):
    return User.objects.create_user(
        email="existing@example.com",
        password="goodpassword123",
        first_name="Existing",
        last_name="User",
    )


@pytest.mark.django_db
class TestRegister:
    url = "/api/v1/auth/register/"

    def test_register_creates_user(self, client):
        response = client.post(
            self.url,
            {"email": "new@example.com", "password": "securepass123", "first_name": "New"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert User.objects.filter(email="new@example.com").exists()

    def test_register_sets_refresh_cookie(self, client):
        response = client.post(
            self.url,
            {"email": "cookie@example.com", "password": "securepass123"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "refresh_token" in response.cookies

    def test_register_duplicate_email(self, client, existing_user):
        response = client.post(
            self.url,
            {"email": existing_user.email, "password": "otherpass123"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, client):
        response = client.post(self.url, {"email": "weak@example.com", "password": "123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_email(self, client):
        response = client.post(self.url, {"password": "goodpassword123"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_creates_tenant(self, client):
        from apps.tenants.models import Tenant

        client.post(
            self.url,
            {"email": "tenant@example.com", "password": "securepass123"},
        )
        assert Tenant.objects.filter(owner__email="tenant@example.com").exists()

    def test_register_creates_admin_membership(self, client):
        from apps.tenants.models import TenantMembership

        client.post(
            self.url,
            {"email": "member@example.com", "password": "securepass123"},
        )
        user = User.objects.get(email="member@example.com")
        membership = TenantMembership.objects.filter(user=user).first()
        assert membership is not None
        assert membership.role == TenantMembership.Role.ADMIN


@pytest.mark.django_db
class TestLogin:
    url = "/api/v1/auth/login/"

    def test_login_success(self, client, existing_user):
        response = client.post(
            self.url, {"email": existing_user.email, "password": "goodpassword123"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, client, existing_user):
        response = client.post(
            self.url, {"email": existing_user.email, "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_unknown_email(self, client):
        response = client.post(
            self.url, {"email": "ghost@example.com", "password": "anypassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, client, existing_user):
        existing_user.is_active = False
        existing_user.save()
        response = client.post(
            self.url, {"email": existing_user.email, "password": "goodpassword123"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogout:
    url = "/api/v1/auth/logout/"

    def test_logout_clears_cookie(self, client, existing_user):
        # Login first
        login_resp = client.post(
            "/api/v1/auth/login/",
            {"email": existing_user.email, "password": "goodpassword123"},
        )
        access = login_resp.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_logout_requires_auth(self, client):
        response = client.post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    url = "/api/v1/auth/token/refresh/"

    def test_refresh_with_valid_cookie(self, client, existing_user):
        refresh = RefreshToken.for_user(existing_user)
        client.cookies["refresh_token"] = str(refresh)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_without_cookie(self, client):
        response = client.post(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordReset:
    request_url = "/api/v1/auth/password-reset/"

    def test_reset_request_existing_email(self, client, existing_user):
        response = client.post(self.request_url, {"email": existing_user.email})
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data

    def test_reset_request_unknown_email(self, client):
        # Should return 200 to prevent enumeration
        response = client.post(self.request_url, {"email": "nobody@example.com"})
        assert response.status_code == status.HTTP_200_OK
