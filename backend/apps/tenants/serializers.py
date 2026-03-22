"""
Tenant serializers.
"""
from rest_framework import serializers

from apps.tenants.models import Tenant, TenantMembership
from apps.users.serializers import UserSerializer


class TenantSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "owner", "created_at", "updated_at"]


class TenantMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "user", "tenant_name", "role", "created_at"]
        read_only_fields = ["id", "user", "tenant_name", "created_at"]
