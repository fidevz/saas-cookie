"""
Tests for notification views.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.models import Notification

User = get_user_model()

FEATURES_ON = {"FEATURE_FLAGS": {"TEAMS": True, "BILLING": True, "NOTIFICATIONS": True}}
FEATURES_OFF = {
    "FEATURE_FLAGS": {"TEAMS": False, "BILLING": False, "NOTIFICATIONS": False}
}


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def user(db):
    return User.objects.create_user(email="notif@example.com", password="pass123")


@pytest.fixture
def notifications(db, user):
    return [
        Notification.objects.create(
            user=user, type="info", title=f"Notif {i}", body="body"
        )
        for i in range(3)
    ]


@pytest.mark.django_db
class TestListNotificationsView:
    url = "/api/v1/notifications/"

    @override_settings(**FEATURES_ON)
    def test_list_returns_notifications(self, user, notifications):
        client = auth_client(user)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    @override_settings(**FEATURES_ON)
    def test_unauthenticated_returns_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(**FEATURES_OFF)
    def test_feature_disabled_returns_403(self, user):
        client = auth_client(user)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(**FEATURES_ON)
    def test_only_own_notifications(self, user, notifications, db):
        other = User.objects.create_user(email="other@example.com", password="pass")
        Notification.objects.create(user=other, type="info", title="Other", body="")
        client = auth_client(user)
        response = client.get(self.url)
        assert response.data["count"] == 3


@pytest.mark.django_db
class TestMarkReadView:
    @override_settings(**FEATURES_ON)
    def test_mark_single_read(self, user, notifications):
        notif = notifications[0]
        assert notif.read is False
        client = auth_client(user)
        response = client.patch(f"/api/v1/notifications/{notif.pk}/read/")
        assert response.status_code == status.HTTP_200_OK
        notif.refresh_from_db()
        assert notif.read is True

    @override_settings(**FEATURES_ON)
    def test_mark_other_users_notification_returns_404(self, user, db):
        other = User.objects.create_user(email="other2@example.com", password="pass")
        notif = Notification.objects.create(user=other, type="info", title="X", body="")
        client = auth_client(user)
        response = client.patch(f"/api/v1/notifications/{notif.pk}/read/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMarkAllReadView:
    url = "/api/v1/notifications/read-all/"

    @override_settings(**FEATURES_ON)
    def test_mark_all_read(self, user, notifications):
        client = auth_client(user)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert Notification.objects.filter(user=user, read=False).count() == 0

    @override_settings(**FEATURES_ON)
    def test_unauthenticated_returns_401(self):
        response = APIClient().post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDeleteNotificationView:
    @override_settings(**FEATURES_ON)
    def test_delete_own_notification(self, user, notifications):
        notif = notifications[0]
        client = auth_client(user)
        response = client.delete(f"/api/v1/notifications/{notif.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(pk=notif.pk).exists()

    @override_settings(**FEATURES_ON)
    def test_delete_other_users_notification_returns_404(self, user, db):
        other = User.objects.create_user(email="other3@example.com", password="pass")
        notif = Notification.objects.create(user=other, type="info", title="X", body="")
        client = auth_client(user)
        response = client.delete(f"/api/v1/notifications/{notif.pk}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(**FEATURES_ON)
    def test_unauthenticated_returns_401(self, notifications):
        response = APIClient().delete(f"/api/v1/notifications/{notifications[0].pk}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(**FEATURES_OFF)
    def test_feature_disabled_returns_403(self, user, notifications):
        client = auth_client(user)
        response = client.delete(f"/api/v1/notifications/{notifications[0].pk}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestClearReadNotificationsView:
    url = "/api/v1/notifications/clear-read/"

    @override_settings(**FEATURES_ON)
    def test_clear_read_deletes_only_read(self, user, notifications):
        # Mark 2 of 3 as read
        Notification.objects.filter(
            pk__in=[notifications[0].pk, notifications[1].pk]
        ).update(read=True)
        client = auth_client(user)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert Notification.objects.filter(user=user).count() == 1
        assert Notification.objects.filter(user=user, read=False).count() == 1

    @override_settings(**FEATURES_ON)
    def test_clear_read_when_none_read(self, user, notifications):
        client = auth_client(user)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "0 read notifications cleared."
        assert Notification.objects.filter(user=user).count() == 3

    @override_settings(**FEATURES_ON)
    def test_unauthenticated_returns_401(self):
        response = APIClient().post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCreateWebSocketTicketView:
    url = "/api/v1/notifications/ws-ticket/"

    @override_settings(**FEATURES_ON)
    def test_authenticated_returns_ticket(self, user):
        from django.core.cache import cache

        client = auth_client(user)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "ticket" in response.data
        ticket = response.data["ticket"]
        # Ticket must be stored in cache
        cached = cache.get(f"ws_ticket:{ticket}")
        assert cached is not None
        assert cached["user_id"] == user.pk

    @override_settings(**FEATURES_ON)
    def test_unauthenticated_returns_401(self):
        response = APIClient().post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(**FEATURES_OFF)
    def test_feature_disabled_returns_403(self, user):
        client = auth_client(user)
        response = client.post(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
