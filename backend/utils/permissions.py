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


class _HasPlanCapabilityPermission(BasePermission):
    """Internal class produced by HasPlanCapability factory."""

    capability_key: str = ""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        from apps.subscriptions.models import Plan, Subscription

        try:
            subscription = Subscription.objects.select_related("plan").get(tenant=tenant)
        except Subscription.DoesNotExist:
            return True  # No subscription means no billing restrictions

        if not subscription.is_active:
            return False

        # Use snapshot capabilities; fall back to the live plan if snapshot is empty.
        caps = subscription.capabilities or (
            subscription.plan.capabilities if subscription.plan else {}
        )

        if caps.get(self.capability_key):
            return True

        # Build a structured 403 with the list of plans that include this capability.
        required_plans = list(
            Plan.objects.filter(
                is_active=True,
                **{f"capabilities__{self.capability_key}": True},
            ).values("id", "name")
        )
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            {
                "code": "plan_capability_required",
                "capability": self.capability_key,
                "required_plans": required_plans,
            }
        )


def HasPlanCapability(capability_key: str) -> type:
    """
    Factory that returns a DRF permission class checking a boolean plan capability.

    On denial returns HTTP 403 with::

        {
            "code": "plan_capability_required",
            "capability": "<key>",
            "required_plans": [{"id": 2, "name": "Pro"}, ...]
        }

    Usage::

        permission_classes = [IsTenantMember, HasPlanCapability("teams")]
    """
    return type(
        f"HasPlanCapability_{capability_key}",
        (_HasPlanCapabilityPermission,),
        {"capability_key": capability_key},
    )


class _WithinPlanLimitPermission(BasePermission):
    """Internal class produced by WithinPlanLimit factory."""

    capability_key: str = ""
    count_fn = None  # callable(tenant) -> int

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        from apps.subscriptions.models import Plan, Subscription

        try:
            subscription = Subscription.objects.select_related("plan").get(tenant=tenant)
        except Subscription.DoesNotExist:
            return True  # No subscription means no billing restrictions

        if not subscription.is_active:
            return False

        caps = subscription.capabilities or (
            subscription.plan.capabilities if subscription.plan else {}
        )
        limit = caps.get(self.capability_key)

        if limit is None:
            return True  # null = unlimited

        current = self.count_fn(tenant) if self.count_fn else 0

        if current < limit:
            return True

        # Build a structured 403 showing plans with a higher limit.
        required_plans = list(
            Plan.objects.filter(
                is_active=True,
                **{f"capabilities__{self.capability_key}__gt": limit},
            ).values("id", "name")
            | Plan.objects.filter(
                is_active=True,
                **{f"capabilities__{self.capability_key}__isnull": True},
            ).values("id", "name")
        )
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied(
            {
                "code": "plan_limit_exceeded",
                "capability": self.capability_key,
                "limit": limit,
                "current": current,
                "required_plans": required_plans,
            }
        )


def WithinPlanLimit(capability_key: str, count_fn) -> type:
    """
    Factory that returns a DRF permission class checking a numeric plan limit.

    ``count_fn(tenant) -> int`` should return the current usage count.
    A stored limit of ``None`` is treated as unlimited (always passes).

    On denial returns HTTP 403 with::

        {
            "code": "plan_limit_exceeded",
            "capability": "<key>",
            "limit": 5,
            "current": 5,
            "required_plans": [{"id": 3, "name": "Elite"}, ...]
        }

    Usage::

        from apps.tenants.models import TenantMembership
        permission_classes = [
            IsTenantAdmin,
            HasPlanCapability("teams"),
            WithinPlanLimit("team_members", lambda t: TenantMembership.objects.filter(tenant=t).count()),
        ]
    """
    return type(
        f"WithinPlanLimit_{capability_key}",
        (_WithinPlanLimitPermission,),
        {"capability_key": capability_key, "count_fn": staticmethod(count_fn)},
    )
