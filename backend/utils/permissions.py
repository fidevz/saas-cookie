"""
Custom DRF permission classes for tenant-scoped access control.
"""
from rest_framework.permissions import BasePermission


class IsTenantMember(BasePermission):
    """
    Allow access only to authenticated users who are members of the current tenant.
    """

    message = "You must be a member of this tenant."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        from apps.tenants.models import TenantMembership

        return TenantMembership.objects.filter(
            user=request.user, tenant=tenant
        ).exists()


class IsTenantAdmin(BasePermission):
    """
    Allow access only to authenticated users who are admins of the current tenant.
    """

    message = "You must be an admin of this tenant."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        from apps.tenants.models import TenantMembership

        return TenantMembership.objects.filter(
            user=request.user,
            tenant=tenant,
            role=TenantMembership.Role.ADMIN,
        ).exists()


class IsSubscriptionActive(BasePermission):
    """
    Allow access only when the current tenant has an active subscription.
    """

    message = "An active subscription is required."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        from apps.subscriptions.models import Subscription

        try:
            subscription = Subscription.objects.get(tenant=tenant)
            return subscription.is_active
        except Subscription.DoesNotExist:
            return False


class _FeatureEnabledPermission(BasePermission):
    """Internal permission class produced by FeatureEnabled factory."""

    feature_name: str = ""
    message = ""

    def has_permission(self, request, view) -> bool:
        from apps.core.features import FeatureFlags

        return FeatureFlags.get_feature(self.feature_name)


def FeatureEnabled(feature_name: str) -> type:
    """
    Factory that returns a DRF permission class which checks a feature flag.

    Usage::

        permission_classes = [IsAuthenticated, FeatureEnabled("TEAMS")]
    """
    name = feature_name.upper()
    return type(
        f"FeatureEnabled_{name}",
        (_FeatureEnabledPermission,),
        {
            "feature_name": name,
            "message": f"Feature '{name}' is not enabled.",
        },
    )
