"""
Tests for the seed management command.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
class TestSeedCommand:
    def test_seed_creates_admin_user(self):
        call_command("seed", verbosity=0)
        assert User.objects.filter(email="admin@test.com").exists()

    def test_seed_creates_plans(self):
        from apps.subscriptions.models import Plan

        call_command("seed", verbosity=0)
        assert Plan.objects.count() >= 2
        assert Plan.objects.filter(name="Starter").exists()
        assert Plan.objects.filter(name="Pro").exists()

    def test_seed_creates_tenant(self):
        from apps.tenants.models import Tenant

        call_command("seed", verbosity=0)
        assert Tenant.objects.filter(slug="test-company").exists()

    def test_seed_creates_admin_membership(self):
        from apps.tenants.models import TenantMembership

        call_command("seed", verbosity=0)
        user = User.objects.get(email="admin@test.com")
        assert TenantMembership.objects.filter(
            user=user,
            role=TenantMembership.Role.ADMIN,
        ).exists()

    def test_seed_is_idempotent(self):
        """Running seed twice should not raise errors or create duplicates."""
        call_command("seed", verbosity=0)
        call_command("seed", verbosity=0)
        assert User.objects.filter(email="admin@test.com").count() == 1
