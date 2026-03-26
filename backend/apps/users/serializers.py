"""
User serializers.
"""
from rest_framework import serializers

from apps.users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation used in responses and dj-rest-auth."""

    tenant_slug = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["id", "email", "pending_email", "first_name", "last_name", "is_first_login", "date_joined", "tenant_slug", "theme"]
        read_only_fields = ["id", "email", "pending_email", "is_first_login", "date_joined", "tenant_slug"]

    def get_tenant_slug(self, obj: CustomUser) -> str | None:
        membership = (
            obj.tenant_memberships.select_related("tenant")
            .order_by("created_at")
            .first()
        )
        return membership.tenant.slug if membership else None


class UserProfileSerializer(serializers.ModelSerializer):
    """Writable serializer for the authenticated user's own profile."""

    tenant_slug = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["id", "email", "pending_email", "first_name", "last_name", "is_first_login", "tenant_slug", "theme"]
        read_only_fields = ["id", "email", "pending_email", "is_first_login", "tenant_slug"]

    def get_tenant_slug(self, obj: CustomUser) -> str | None:
        membership = (
            obj.tenant_memberships.select_related("tenant")
            .order_by("created_at")
            .first()
        )
        return membership.tenant.slug if membership else None

    def validate_first_name(self, value: str) -> str:
        return value.strip()

    def validate_last_name(self, value: str) -> str:
        return value.strip()
