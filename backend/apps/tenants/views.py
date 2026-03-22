"""
Tenant views.
"""
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.serializers import TenantMembershipSerializer, TenantSerializer
from utils.permissions import IsTenantAdmin, IsTenantMember


class TenantDetailView(RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/tenants/current/ — retrieve or update the current tenant."""

    serializer_class = TenantSerializer
    permission_classes = [IsTenantAdmin]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self) -> Tenant:
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("No tenant found for this request.")
        self.check_object_permissions(self.request, tenant)
        return tenant


class TenantMembershipListView(ListAPIView):
    """GET /api/v1/tenants/members/ — list all members of the current tenant."""

    serializer_class = TenantMembershipSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            return TenantMembership.objects.none()
        return (
            TenantMembership.objects.filter(tenant=tenant)
            .select_related("user", "tenant")
            .order_by("created_at")
        )
