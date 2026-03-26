"""
WebSocket consumer for real-time notifications.

Connect URL: ws://host/ws/notifications/?ticket=<single_use_uuid>

The ticket is obtained via POST /api/v1/notifications/ws-ticket/ and is valid for 30 seconds.
Tickets are single-use — consumed immediately on connection to prevent replay attacks.
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Authenticated WebSocket consumer.

    Authentication: single-use ticket passed as query parameter ``ticket``.
    Group: ``notifications_{user_id}``
    """

    async def connect(self):
        user, tenant = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        # Enforce per-user concurrent connection limit
        conn_key = f"ws_active:{user.pk}"
        if not await self._increment_connection(conn_key, user.pk):
            await self.close(code=4008)
            return

        self.user = user
        self.tenant = tenant
        self._conn_cache_key = conn_key  # Used in disconnect() for cleanup
        self.group_name = f"notifications_{user.pk}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WebSocket connected: user=%s group=%s", user.pk, self.group_name)

    async def disconnect(self, close_code):
        group = getattr(self, "group_name", None)
        if group:
            await self.channel_layer.group_discard(group, self.channel_name)
        # Decrement connection counter only if we successfully incremented it
        if hasattr(self, "_conn_cache_key"):
            await self._decrement_connection(self._conn_cache_key)
        logger.debug("WebSocket disconnected: code=%s", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        """Handle messages from the client (e.g. mark_read)."""
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON"}))
            return

        action = data.get("action")
        if action == "mark_read":
            await self._mark_read(data.get("notification_id"))
        else:
            await self.send(json.dumps({"error": f"Unknown action: {action}"}))

    # ------------------------------------------------------------------
    # Channel layer message handlers
    # ------------------------------------------------------------------

    async def notification_message(self, event):
        """Called by channel_layer.group_send with type='notification.message'."""
        await self.send(
            json.dumps(
                {
                    "type": "notification",
                    "notification": event.get("notification", {}),
                }
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _increment_connection(self, cache_key: str, user_pk: int) -> bool:
        """Atomically increment the per-user connection counter.

        Returns True if the connection is allowed, False if the limit is exceeded.
        """
        from asgiref.sync import sync_to_async
        from django.core.cache import cache

        limit = getattr(settings, "WS_MAX_CONNECTIONS_PER_USER", 15)

        @sync_to_async(thread_sensitive=False)
        def do_increment():
            # cache.add is a no-op if the key already exists — safe to seed
            cache.add(cache_key, 0, timeout=86400)
            count = cache.incr(cache_key)
            if count > limit:
                cache.decr(cache_key)  # Undo; connection is not allowed
                logger.warning(
                    "WebSocket rate limit exceeded: user=%s active=%d limit=%d",
                    user_pk,
                    count,
                    limit,
                )
                return False
            return True

        return await do_increment()

    async def _decrement_connection(self, cache_key: str) -> None:
        """Decrement the per-user connection counter on disconnect."""
        from asgiref.sync import sync_to_async
        from django.core.cache import cache

        @sync_to_async(thread_sensitive=False)
        def do_decrement():
            try:
                cache.decr(cache_key)
            except Exception:
                pass  # Key may have expired; not critical

        await do_decrement()

    async def _authenticate(self):
        """Redeem a single-use WebSocket ticket from the query string.

        The ticket was minted by POST /api/v1/notifications/ws-ticket/ and stored
        in Redis cache with a 30-second TTL. It is deleted immediately on use to
        prevent replay attacks.

        Returns a (user, tenant) tuple, or (None, None) on failure.
        """
        from urllib.parse import parse_qs

        from asgiref.sync import sync_to_async
        from django.core.cache import cache

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        ticket_list = params.get("ticket", [])

        if not ticket_list:
            logger.debug("WebSocket connection rejected: no ticket provided")
            return None, None

        ticket = ticket_list[0]
        cache_key = f"ws_ticket:{ticket}"

        @sync_to_async(thread_sensitive=False)
        def redeem_ticket(key):
            payload = cache.get(key)
            if payload is None:
                return None
            cache.delete(key)  # Single-use: consume immediately
            return payload.get("user_id")

        user_id = await redeem_ticket(cache_key)
        if user_id is None:
            logger.debug("WebSocket connection rejected: invalid or expired ticket")
            return None, None

        @sync_to_async(thread_sensitive=False)
        def get_user_and_tenant(uid):
            user = NotificationConsumer._get_user(uid)
            if user is None:
                return None, None
            tenant = NotificationConsumer._get_tenant_for_user(user)
            return user, tenant

        return await get_user_and_tenant(user_id)

    @staticmethod
    def _get_user(user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _get_tenant_for_user(user):
        from apps.tenants.models import TenantMembership

        membership = (
            TenantMembership.objects.filter(user=user).select_related("tenant").first()
        )
        return membership.tenant if membership else None

    async def _mark_read(self, notification_id):
        if not notification_id:
            return

        from asgiref.sync import sync_to_async

        from apps.notifications.models import Notification

        @sync_to_async
        def do_mark(nid, user, tenant):
            # Filter by tenant to prevent cross-tenant notification manipulation.
            qs = Notification.objects.filter(pk=nid, user=user)
            if tenant is not None:
                qs = qs.filter(tenant=tenant)
            qs.update(read=True)

        await do_mark(notification_id, self.user, self.tenant)
        await self.send(
            json.dumps({"type": "marked_read", "notification_id": notification_id})
        )
