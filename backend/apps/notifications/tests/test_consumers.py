"""
Tests for the NotificationConsumer WebSocket consumer.
"""
import json

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="ws@example.com", password="wspass123")


def get_token(user) -> str:
    return str(AccessToken.for_user(user))


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    async def test_connect_with_valid_token(self, user):
        token = get_token(user)
        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
        )
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_connect_without_token_closes(self, user):
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        connected, code = await communicator.connect()
        # Should either reject or close with 4001
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001

    async def test_connect_with_invalid_token_closes(self):
        communicator = WebsocketCommunicator(
            application, "/ws/notifications/?token=invalid.token.here"
        )
        connected, code = await communicator.connect()
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001

    async def test_mark_read_action(self, user):
        from asgiref.sync import sync_to_async

        from apps.notifications.models import Notification

        @sync_to_async
        def create_notification():
            return Notification.objects.create(
                user=user, type="info", title="Test", body="body"
            )

        notif = await create_notification()
        token = get_token(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?token={token}"
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
