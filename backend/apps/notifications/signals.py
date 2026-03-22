"""
Signals for the notifications app.

Sends a welcome notification when a user logs in for the first time.
"""
import asyncio
import logging

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def send_welcome_notification(sender, request, user, **kwargs):
    """Fire a welcome notification on first login."""
    if not user.is_first_login:
        return

    app_name = settings.APP_NAME

    try:
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            type=Notification.Type.WELCOME,
            title=f"Welcome to {app_name}!",
            body=(
                f"Hi {user.first_name or user.email}, welcome aboard! "
                f"We're excited to have you. Get started by exploring the dashboard."
            ),
        )

        # Push to WebSocket group
        _push_to_websocket(user.pk, notification)

    except Exception as exc:
        # Signals should not crash the login flow
        logger.exception("Failed to create welcome notification for user %s: %s", user.pk, exc)
    finally:
        # Mark first login as done
        user.is_first_login = False
        user.save(update_fields=["is_first_login"])


def _push_to_websocket(user_pk: int, notification) -> None:
    """Attempt to send a real-time notification through the channel layer."""
    try:
        from channels.layers import get_channel_layer
        from apps.notifications.serializers import NotificationSerializer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        group_name = f"notifications_{user_pk}"
        payload = {
            "type": "notification.message",
            "notification": NotificationSerializer(notification).data,
        }
        async_to_sync(channel_layer.group_send)(group_name, payload)
    except Exception as exc:
        logger.warning("Could not push notification to WebSocket: %s", exc)
