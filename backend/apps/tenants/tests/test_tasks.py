"""
Tests for tenant periodic tasks.
"""

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.tasks import cleanup_unverified_tenants

User = get_user_model()


def make_user(email, verified=False, **kwargs):
    user = User.objects.create_user(email=email, password="pass", **kwargs)
    EmailAddress.objects.create(user=user, email=email, verified=verified, primary=True)
    return user


def make_tenant(owner, slug, hours_old=0):
    tenant = Tenant.objects.create(name=slug, slug=slug, owner=owner)
    if hours_old:
        Tenant.objects.filter(pk=tenant.pk).update(
            created_at=timezone.now() - timezone.timedelta(hours=hours_old)
        )
        tenant.refresh_from_db()
    return tenant


@pytest.mark.django_db
class TestCleanupUnverifiedTenants:
    def test_deletes_unverified_tenant_past_grace_period(self, settings):
        settings.UNVERIFIED_TENANT_CLEANUP_HOURS = 48
        owner = make_user("unverified@example.com", verified=False)
        tenant = make_tenant(owner, "unverified-co", hours_old=49)

        cleanup_unverified_tenants()

        assert not Tenant.objects.filter(pk=tenant.pk).exists()
        assert not User.objects.filter(pk=owner.pk).exists()

    def test_keeps_verified_tenant(self, settings):
        settings.UNVERIFIED_TENANT_CLEANUP_HOURS = 48
        owner = make_user("verified@example.com", verified=True)
        tenant = make_tenant(owner, "verified-co", hours_old=72)

        cleanup_unverified_tenants()

        assert Tenant.objects.filter(pk=tenant.pk).exists()
        assert User.objects.filter(pk=owner.pk).exists()

    def test_keeps_unverified_tenant_within_grace_period(self, settings):
        settings.UNVERIFIED_TENANT_CLEANUP_HOURS = 48
        owner = make_user("recent@example.com", verified=False)
        tenant = make_tenant(owner, "recent-co", hours_old=10)

        cleanup_unverified_tenants()

        assert Tenant.objects.filter(pk=tenant.pk).exists()
        assert User.objects.filter(pk=owner.pk).exists()

    def test_keeps_user_with_remaining_membership(self, settings):
        settings.UNVERIFIED_TENANT_CLEANUP_HOURS = 48
        # Owner of another (verified) tenant
        other_owner = make_user("other-owner@example.com", verified=True)
        other_tenant = make_tenant(other_owner, "other-co")

        # The unverified owner is also a member of the other tenant
        owner = make_user("member@example.com", verified=False)
        TenantMembership.objects.create(
            user=owner, tenant=other_tenant, role=TenantMembership.Role.MEMBER
        )
        stale_tenant = make_tenant(owner, "stale-co", hours_old=72)

        cleanup_unverified_tenants()

        assert not Tenant.objects.filter(pk=stale_tenant.pk).exists()
        # User kept because they still have a membership on other_tenant
        assert User.objects.filter(pk=owner.pk).exists()

    def test_invite_flow_user_unaffected(self, settings):
        settings.UNVERIFIED_TENANT_CLEANUP_HOURS = 48
        # Invited users are verified but own no tenant
        invited = make_user("invited@example.com", verified=True)

        cleanup_unverified_tenants()

        assert User.objects.filter(pk=invited.pk).exists()
