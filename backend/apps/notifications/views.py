"""
Notification views.
"""
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.features import FeatureFlags
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


def _require_feature() -> None:
    if not FeatureFlags.notifications_enabled():
        raise PermissionDenied("Notifications feature is not enabled.")


class ListNotificationsView(ListAPIView):
    """GET /api/v1/notifications/ — paginated list, newest first."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        _require_feature()
        return (
            Notification.objects.filter(user=self.request.user)
            .order_by("-created_at")
        )


class MarkReadView(APIView):
    """PATCH /api/v1/notifications/{id}/read/ — mark a single notification as read."""

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, pk: int) -> Response:
        _require_feature()
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        notification.read = True
        notification.save(update_fields=["read"])
        return Response(NotificationSerializer(notification).data)


class MarkAllReadView(APIView):
    """POST /api/v1/notifications/read-all/ — mark all notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        _require_feature()
        updated = Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"detail": f"{updated} notifications marked as read."})
