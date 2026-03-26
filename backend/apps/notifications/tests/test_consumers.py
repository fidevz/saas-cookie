"""
Tests for the NotificationConsumer WebSocket consumer.
"""

import uuid

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connections

from config.asgi import application

User = get_user_model()

# AllowedHostsOriginValidator requires an Origin header — provide one in tests.
WS_HEADERS = [(b"origin", b"http://localhost")]


@pytest.fixture
def user(transactional_db):
    return User.objects.create_user(email="ws@example.com", password="wspass123")


def get_ticket(user) -> str:
    """Create a single-use WebSocket ticket in cache and return the UUID."""
    ticket = str(uuid.uuid4())
    cache.set(f"ws_ticket:{ticket}", {"user_id": user.pk}, timeout=30)
    return ticket


@sync_to_async
def close_db_connections():
    """Close all DB connections so pytest-django can drop the test DB."""
    for conn in connections.all():
        conn.close()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    async def test_connect_with_valid_ticket(self, user):
        ticket = get_ticket(user)
        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?ticket={ticket}", headers=WS_HEADERS
        )
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()
        await close_db_connections()

    async def test_connect_without_ticket_closes(self, user):
        communicator = WebsocketCommunicator(
            application, "/ws/notifications/", headers=WS_HEADERS
        )
        connected, code = await communicator.connect()
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001
        await close_db_connections()

    async def test_connect_with_invalid_ticket_closes(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/notifications/?ticket=nonexistent-uuid",
            headers=WS_HEADERS,
        )
        connected, code = await communicator.connect()
        if connected:
            await communicator.disconnect()
        else:
            assert code == 4001
        await close_db_connections()

    async def test_ticket_is_single_use(self, user):
        ticket = get_ticket(user)
        # First connection consumes the ticket
        c1 = WebsocketCommunicator(
            application, f"/ws/notifications/?ticket={ticket}", headers=WS_HEADERS
        )
        connected, _ = await c1.connect()
        assert connected
        await c1.disconnect()

        # Second connection with the same ticket must fail
        c2 = WebsocketCommunicator(
            application, f"/ws/notifications/?ticket={ticket}", headers=WS_HEADERS
        )
        connected2, code = await c2.connect()
        if connected2:
            await c2.disconnect()
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
        ticket = get_ticket(user)

        communicator = WebsocketCommunicator(
            application, f"/ws/notifications/?ticket={ticket}", headers=WS_HEADERS
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


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumerRateLimit:
    """Tests for the per-user concurrent connection limit."""

    @sync_to_async
    def clear_conn_key(self, user_pk):
        cache.delete(f"ws_active:{user_pk}")

    async def test_connections_within_limit_are_accepted(self, user):
        """Connections up to the limit (overridden to 2) must all succeed."""
        from django.test import override_settings

        with override_settings(WS_MAX_CONNECTIONS_PER_USER=2):
            await self.clear_conn_key(user.pk)
            communicators = []
            for _ in range(2):
                c = WebsocketCommunicator(
                    application,
                    f"/ws/notifications/?ticket={get_ticket(user)}",
                    headers=WS_HEADERS,
                )
                connected, _ = await c.connect()
                assert connected
                communicators.append(c)

            for c in communicators:
                await c.disconnect()
        await close_db_connections()

    async def test_connection_over_limit_is_rejected(self, user):
        """The (limit+1)th connection must be rejected with close code 4008."""
        from django.test import override_settings

        with override_settings(WS_MAX_CONNECTIONS_PER_USER=2):
            await self.clear_conn_key(user.pk)
            allowed = []
            for _ in range(2):
                c = WebsocketCommunicator(
                    application,
                    f"/ws/notifications/?ticket={get_ticket(user)}",
                    headers=WS_HEADERS,
                )
                connected, _ = await c.connect()
                assert connected
                allowed.append(c)

            # One over the limit
            over = WebsocketCommunicator(
                application,
                f"/ws/notifications/?ticket={get_ticket(user)}",
                headers=WS_HEADERS,
            )
            connected, code = await over.connect()
            if connected:
                await over.disconnect()
            else:
                assert code == 4008

            for c in allowed:
                await c.disconnect()
        await close_db_connections()

    async def test_disconnect_frees_slot(self, user):
        """After disconnecting one connection, a new one should be accepted."""
        from django.test import override_settings

        with override_settings(WS_MAX_CONNECTIONS_PER_USER=2):
            await self.clear_conn_key(user.pk)
            c1 = WebsocketCommunicator(
                application,
                f"/ws/notifications/?ticket={get_ticket(user)}",
                headers=WS_HEADERS,
            )
            c2 = WebsocketCommunicator(
                application,
                f"/ws/notifications/?ticket={get_ticket(user)}",
                headers=WS_HEADERS,
            )
            connected1, _ = await c1.connect()
            connected2, _ = await c2.connect()
            assert connected1 and connected2

            # Disconnect one slot
            await c1.disconnect()

            # New connection should now succeed
            c3 = WebsocketCommunicator(
                application,
                f"/ws/notifications/?ticket={get_ticket(user)}",
                headers=WS_HEADERS,
            )
            connected3, _ = await c3.connect()
            assert connected3
            await c2.disconnect()
            await c3.disconnect()
        await close_db_connections()
