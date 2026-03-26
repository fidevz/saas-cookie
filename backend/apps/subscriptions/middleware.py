"""
Optional subscription paywall middleware.

Active only when FEATURE_REQUIRE_SUBSCRIPTION=True.
Returns HTTP 402 for authenticated requests to tenants without an active subscription.
"""
import json

from django.http import HttpResponse

from apps.core.features import FeatureFlags

# Paths that never require a subscription check
_EXEMPT_PREFIXES = (
    "/health",
    "/api/v1/auth/",
    "/api/v1/features/",
    "/api/v1/subscriptions/",  # Allow purchasing / checking status
    "/api/v1/support/",
    "/api/v1/users/me",  # Profile — needed for auth initialization
    "/api/v1/tenants/members/",  # Role check — needed for layout
    "/api/v1/notifications/",  # Notifications — loaded in layout
    "/api/docs/",
    "/api/schema/",
)


class SubscriptionPaywallMiddleware:
    """
    When REQUIRE_SUBSCRIPTION is enabled, any authenticated API request
    to a tenant without an active subscription receives HTTP 402.

    Exemptions: auth endpoints, features, subscriptions, support, docs, health,
    and the admin URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_block(request):
            body = json.dumps({
                "code": "subscription_required",
                "detail": "An active subscription is required to use this feature.",
            })
            return HttpResponse(body, status=402, content_type="application/json")

        return self.get_response(request)

    def _should_block(self, request) -> bool:
        # Feature flag off → never block
        if not FeatureFlags.require_subscription():
            return False

        # Only enforce on API paths
        if not request.path.startswith("/api/"):
            return False

        # No tenant context → root domain, don't block
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        # Exempt specific prefixes
        for prefix in _EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return False

        # Only block authenticated requests (unauthenticated handled by auth middleware)
        if not request.headers.get("Authorization", "").startswith("Bearer "):
            return False

        # Check for active subscription
        from apps.subscriptions.models import Subscription
        has_active = Subscription.objects.filter(
            tenant=tenant,
            status__in=[
                Subscription.Status.ACTIVE,
                Subscription.Status.TRIALING,
                Subscription.Status.CANCELLING,
            ],
        ).exists()

        return not has_active
