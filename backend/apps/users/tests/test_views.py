"""
Tests for user profile views.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import signing
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def get_auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="profile@example.com",
        password="testpass123",
        first_name="Alice",
        last_name="Smith",
    )


@pytest.mark.django_db
class TestProfileView:
    def test_get_profile(self, user):
        client = get_auth_client(user)
        url = reverse("user-profile")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == "Alice"

    def test_get_profile_unauthenticated(self):
        client = APIClient()
        url = reverse("user-profile")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_profile(self, user):
        client = get_auth_client(user)
        url = reverse("user-profile")
        response = client.patch(url, {"first_name": "Bob", "last_name": "Jones"})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Bob"
        assert user.last_name == "Jones"

    def test_patch_profile_strips_whitespace(self, user):
        client = get_auth_client(user)
        url = reverse("user-profile")
        response = client.patch(url, {"first_name": "  Carol  ", "last_name": "  "})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Carol"
        assert user.last_name == ""

    def test_cannot_change_email_via_patch(self, user):
        client = get_auth_client(user)
        url = reverse("user-profile")
        client.patch(url, {"email": "hacker@evil.com"})
        user.refresh_from_db()
        assert user.email == "profile@example.com"

    def test_put_not_allowed(self, user):
        client = get_auth_client(user)
        url = reverse("user-profile")
        response = client.put(url, {"first_name": "X", "last_name": "Y"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def _make_email_change_token(user, new_email):
    from apps.users.views import EMAIL_CHANGE_SALT

    return signing.dumps({"uid": user.pk, "email": new_email}, salt=EMAIL_CHANGE_SALT)


@pytest.mark.django_db
class TestEmailChangeConfirmStripeSync:
    url = "/api/v1/users/me/email/confirm/"

    @patch("apps.subscriptions.tasks.sync_stripe_customer_email.delay")
    def test_dispatches_stripe_sync_task_on_confirm(self, mock_delay, user):
        user.pending_email = "confirmed@example.com"
        user.save(update_fields=["pending_email"])
        token = _make_email_change_token(user, "confirmed@example.com")

        client = APIClient()
        response = client.post(self.url, {"token": token})

        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_called_once_with(user.pk, "confirmed@example.com")

    @patch("apps.subscriptions.tasks.sync_stripe_customer_email.delay")
    def test_does_not_dispatch_when_billing_disabled(self, mock_delay, user):
        user.pending_email = "confirmed@example.com"
        user.save(update_fields=["pending_email"])
        token = _make_email_change_token(user, "confirmed@example.com")

        client = APIClient()
        with override_settings(
            FEATURE_FLAGS={"TEAMS": True, "BILLING": False, "NOTIFICATIONS": True}
        ):
            response = client.post(self.url, {"token": token})

        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_not_called()
