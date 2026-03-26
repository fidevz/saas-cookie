"""
Celery tasks for tenant management.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def cleanup_unverified_tenants() -> None:
    """
    Delete tenants whose owner never verified their email, after the grace period.

    Cascades to TenantMembership and Subscription. Deletes the owner user if
    they have no remaining tenants or memberships after the tenant is removed.
    """
    from allauth.account.models import EmailAddress

    from apps.tenants.models import Tenant

    grace_hours = getattr(settings, "UNVERIFIED_TENANT_CLEANUP_HOURS", 48)
    cutoff = timezone.now() - timedelta(hours=grace_hours)

    verified_owner_ids = EmailAddress.objects.filter(verified=True).values_list(
        "user_id", flat=True
    )

    stale_tenants = (
        Tenant.objects.filter(created_at__lt=cutoff)
        .exclude(owner_id__in=verified_owner_ids)
        .select_related("owner")
    )

    count = 0
    for tenant in stale_tenants:
        owner = tenant.owner
        tenant.delete()
        if not owner.owned_tenants.exists() and not owner.tenant_memberships.exists():
            owner.delete()
        count += 1

    logger.info("Cleaned up %d unverified tenant(s)", count)
