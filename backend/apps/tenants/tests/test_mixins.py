"""
Tests for TenantManager, TenantModelMixin, and TenantViewMixin.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from apps.tenants.mixins import TenantViewMixin
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.serializers import TenantMembershipSerializer

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@mixin.com", password="pass123")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="other@mixin.com", password="pass123")


@pytest.fixture
def tenant_a(db, owner):
    return Tenant.objects.create(name="TenantA", slug="tenant-a", owner=owner)


@pytest.fixture
def tenant_b(db, other_user):
    return Tenant.objects.create(name="TenantB", slug="tenant-b", owner=other_user)


# ---------------------------------------------------------------------------
# TenantViewMixin — uses TenantMembership which has a tenant FK
# ---------------------------------------------------------------------------


class MembershipListView(TenantViewMixin, ListAPIView):
    queryset = TenantMembership.objects.all()
    serializer_class = TenantMembershipSerializer
    permission_classes = [AllowAny]


@pytest.mark.django_db
class TestTenantViewMixin:
    def _make_view(self, tenant):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.tenant = tenant
        view = MembershipListView()
        view.request = request
        view.kwargs = {}
        view.format_kwarg = None
        return view

    def test_filters_to_request_tenant(self, owner, other_user, tenant_a, tenant_b):
        TenantMembership.objects.create(
            user=owner, tenant=tenant_a, role=TenantMembership.Role.ADMIN
        )
        TenantMembership.objects.create(
            user=other_user, tenant=tenant_b, role=TenantMembership.Role.ADMIN
        )

        view = self._make_view(tenant_a)
        qs = view.get_queryset()

        assert qs.count() == 1
        assert qs.first().tenant == tenant_a

    def test_no_tenant_returns_unfiltered(self, owner, other_user, tenant_a, tenant_b):
        TenantMembership.objects.create(
            user=owner, tenant=tenant_a, role=TenantMembership.Role.ADMIN
        )
        TenantMembership.objects.create(
            user=other_user, tenant=tenant_b, role=TenantMembership.Role.ADMIN
        )

        view = self._make_view(None)
        qs = view.get_queryset()

        assert qs.count() == 2

    def test_returns_all_rows_for_tenant(self, owner, other_user, tenant_a):
        TenantMembership.objects.create(
            user=owner, tenant=tenant_a, role=TenantMembership.Role.ADMIN
        )
        TenantMembership.objects.create(
            user=other_user, tenant=tenant_a, role=TenantMembership.Role.MEMBER
        )

        view = self._make_view(tenant_a)
        qs = view.get_queryset()

        assert qs.count() == 2
