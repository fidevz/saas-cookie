"""
Notification serializers.
"""
from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "body", "read", "created_at"]
        read_only_fields = ["id", "type", "title", "body", "created_at"]
