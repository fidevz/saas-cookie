"""
WebSocket consumer for real-time notifications.

Connect URL: ws://host/ws/notifications/?token=<access_jwt>
"""
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Authenticated WebSocket consumer.

    Authentication: JWT access token passed as query parameter ``token``.
    Group: ``notifications_{user_id}``
    """

    async def connect(self):
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f"notifications_{user.pk}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WebSocket connected: user=%s group=%s", user.pk, self.group_name)

    async def disconnect(self, close_code):
        group = getattr(self, "group_name", None)
        if group:
            await self.channel_layer.group_discard(group, self.channel_name)
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

    async def _authenticate(self):
        """Extract and validate the JWT token from the query string."""
        from urllib.parse import parse_qs

        from asgiref.sync import sync_to_async
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import UntypedToken

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if not token_list:
            logger.debug("WebSocket connection rejected: no token provided")
            return None

        raw_token = token_list[0]
        try:
            UntypedToken(raw_token)
        except (InvalidToken, TokenError) as exc:
            logger.debug("WebSocket auth failed: %s", exc)
            return None

        # Extract user from validated token
        from rest_framework_simplejwt.settings import api_settings as jwt_settings

        try:
            token_backend = jwt_settings.TOKEN_BACKEND
            validated = token_backend.decode(raw_token)
            user_id = validated.get(jwt_settings.USER_ID_CLAIM)
        except Exception:
            return None

        get_user = sync_to_async(self._get_user)
        return await get_user(user_id)

    @staticmethod
    def _get_user(user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None

    async def _mark_read(self, notification_id):
        if not notification_id:
            return

        from asgiref.sync import sync_to_async

        from apps.notifications.models import Notification

        @sync_to_async
        def do_mark(nid, user):
            Notification.objects.filter(pk=nid, user=user).update(read=True)

        await do_mark(notification_id, self.user)
        await self.send(
            json.dumps({"type": "marked_read", "notification_id": notification_id})
        )
