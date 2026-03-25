"""
Team serializers.
"""
from rest_framework import serializers

from apps.teams.models import Invitation
from apps.tenants.models import TenantMembership
from apps.users.serializers import UserSerializer


class InvitationTenantSerializer(serializers.Serializer):
    """Minimal tenant info embedded in invitations."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)


class InvitationSerializer(serializers.ModelSerializer):
    tenant = InvitationTenantSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "role",
            "token",
            "expires_at",
            "accepted",
            "accepted_at",
            "tenant",
            "created_at",
        ]
        read_only_fields = ["id", "token", "expires_at", "accepted", "accepted_at", "tenant", "created_at"]

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_role(self, value: str) -> str:
        if value not in [r[0] for r in TenantMembership.Role.choices]:
            raise serializers.ValidationError("Invalid role.")
        return value


class MemberSerializer(serializers.ModelSerializer):
    """Membership with nested user info."""

    user = UserSerializer(read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "user", "tenant_slug", "role", "created_at"]
        read_only_fields = ["id", "user", "tenant_slug", "created_at"]


class UpdateMemberRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantMembership
        fields = ["role"]

    def validate_role(self, value: str) -> str:
        if value not in [r[0] for r in TenantMembership.Role.choices]:
            raise serializers.ValidationError("Invalid role.")
        return value
