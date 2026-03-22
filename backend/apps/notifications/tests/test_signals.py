"""
Tests for notification signals.

The welcome notification signal fires on `user_logged_in` when the user's
`is_first_login` flag is True. We fire the signal directly (same as Django
does after a successful authentication) to test the signal in isolation
without needing a full HTTP request through the auth stack.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.test import RequestFactory, override_settings

from apps.notifications.models import Notification

User = get_user_model()

APP_NAME = "TestApp"
_SETTINGS = dict(
    APP_NAME=APP_NAME,
    FEATURE_FLAGS={"TEAMS": True, "BILLING": True, "NOTIFICATIONS": True},
)


def fire_login_signal(user):
    """Fire the user_logged_in signal exactly as Django does after login."""
    request = RequestFactory().get("/")
    user_logged_in.send(sender=User, request=request, user=user)


@pytest.fixture
def first_login_user(db):
    """User who has never logged in (is_first_login=True by default)."""
    return User.objects.create_user(
        email="firstlogin@example.com",
        password="pass123",
        first_name="Alice",
    )


@pytest.fixture
def returning_user(db):
    """User who has already completed their first login."""
    user = User.objects.create_user(email="returning@example.com", password="pass123")
    user.is_first_login = False
    user.save()
    return user


@pytest.mark.django_db
class TestWelcomeNotificationSignal:
    @override_settings(**_SETTINGS)
    def test_first_login_creates_welcome_notification(self, first_login_user):
        fire_login_signal(first_login_user)
        assert Notification.objects.filter(
            user=first_login_user, type=Notification.Type.WELCOME
        ).exists()

    @override_settings(**_SETTINGS)
    def test_welcome_notification_title_contains_app_name(self, first_login_user):
        fire_login_signal(first_login_user)
        notif = Notification.objects.get(user=first_login_user, type=Notification.Type.WELCOME)
        assert APP_NAME in notif.title

    @override_settings(**_SETTINGS)
    def test_welcome_notification_body_contains_user_name(self, first_login_user):
        fire_login_signal(first_login_user)
        notif = Notification.objects.get(user=first_login_user, type=Notification.Type.WELCOME)
        assert first_login_user.first_name in notif.body

    @override_settings(**_SETTINGS)
    def test_first_login_flag_set_to_false_after_signal(self, first_login_user):
        assert first_login_user.is_first_login is True
        fire_login_signal(first_login_user)
        first_login_user.refresh_from_db()
        assert first_login_user.is_first_login is False

    @override_settings(**_SETTINGS)
    def test_returning_user_does_not_get_notification(self, returning_user):
        fire_login_signal(returning_user)
        assert not Notification.objects.filter(user=returning_user).exists()

    @override_settings(**_SETTINGS)
    def test_second_login_does_not_create_duplicate(self, first_login_user):
        """Flag is False after first login, so signal is a no-op on subsequent logins."""
        fire_login_signal(first_login_user)
        fire_login_signal(first_login_user)
        assert Notification.objects.filter(user=first_login_user).count() == 1

    @override_settings(**_SETTINGS)
    def test_notification_is_unread_by_default(self, first_login_user):
        fire_login_signal(first_login_user)
        notif = Notification.objects.get(user=first_login_user)
        assert notif.read is False


@pytest.mark.django_db
class TestWelcomeNotificationViaLoginEndpoint:
    """
    End-to-end: first login through the API must create the welcome notification.
    This validates the full stack — signal connected in AppConfig.ready(), DB write
    succeeds, and the is_first_login flag is toggled.
    """

    @override_settings(**_SETTINGS)
    def test_first_api_login_creates_notification(self, db):
        from rest_framework.test import APIClient

        user = User.objects.create_user(
            email="apilogin@example.com",
            password="securepass123",
            first_name="Bob",
        )
        assert user.is_first_login is True

        APIClient().post(
            "/api/v1/auth/login/",
            {"email": "apilogin@example.com", "password": "securepass123"},
        )

        assert Notification.objects.filter(
            user=user, type=Notification.Type.WELCOME
        ).exists()

    @override_settings(**_SETTINGS)
    def test_second_api_login_does_not_duplicate_notification(self, db):
        from rest_framework.test import APIClient

        user = User.objects.create_user(
            email="apilogin2@example.com",
            password="securepass123",
        )
        client = APIClient()
        credentials = {"email": "apilogin2@example.com", "password": "securepass123"}
        client.post("/api/v1/auth/login/", credentials)
        client.post("/api/v1/auth/login/", credentials)

        assert Notification.objects.filter(user=user).count() == 1
