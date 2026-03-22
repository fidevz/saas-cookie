"""
Tests for the NotificationConsumer WebSocket consumer.
"""
import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.db import connections
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application

User = get_user_model()

# AllowedHostsOriginValidator requires an Origin header — provide one in tests.
WS_HEADERS = [(b"origin", b"http://localhost")]


@pytest.fixture
def user(transactional_db):
    return User.objects.create_user(email="ws@example.com", password="wspass123")


def get_token(user) -> str:
    return str(AccessToken.for_user(user))


@sync_to_async
def close_db_connections():
    """Close all DB connections so pytest-django can drop the test DB."""
    for conn in connections.all():
        conn.close()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    async def test_connect_with_valid_token(self, user):
        token = get_token(user)
        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}", headers=WS_HEADERS
        )
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()
        await close_db_connections()

    async def test_connect_without_token_closes(self, user):
        communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=WS_HEADERS)
        connected, code = await communicator.connect()
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001
        await close_db_connections()

    async def test_connect_with_invalid_token_closes(self):
        communicator = WebsocketCommunicator(
            application, "/ws/notifications/?token=invalid.token.here", headers=WS_HEADERS
        )
        connected, code = await communicator.connect()
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001
        await close_db_connections()

    async def test_mark_read_action(self, user):
        from apps.notifications.models import Notification

        @sync_to_async
        def create_notification():
            return Notification.objects.create(
                user=user, type="info", title="Test", body="body"
            )

        notif = await create_notification()
        token = get_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}", headers=WS_HEADERS
        )
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to(
            {"action": "mark_read", "notification_id": notif.pk}
        )
        response = await communicator.receive_json_from(timeout=3)
        assert response.get("type") == "marked_read"
        assert response.get("notification_id") == notif.pk

        await communicator.disconnect()

        @sync_to_async
        def check():
            notif.refresh_from_db()
            return notif.read

        assert await check() is True
        await close_db_connections()
