"""
User serializers.
"""
from rest_framework import serializers

from apps.users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation used in responses and dj-rest-auth."""

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "is_first_login", "date_joined"]
        read_only_fields = ["id", "email", "is_first_login", "date_joined"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Writable serializer for the authenticated user's own profile."""

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "is_first_login"]
        read_only_fields = ["id", "email", "is_first_login"]

    def validate_first_name(self, value: str) -> str:
        return value.strip()

    def validate_last_name(self, value: str) -> str:
        return value.strip()
