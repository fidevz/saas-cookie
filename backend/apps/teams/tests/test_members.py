"""
Tests for member listing, role update, and removal.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@members.com", password="adminpass123")


@pytest.fixture
def member_user(db):
    return User.objects.create_user(email="member@members.com", password="memberpass123")


@pytest.fixture
def tenant(db, admin_user):
    return Tenant.objects.create(name="MemberCorp", slug="membercorp", owner=admin_user)


@pytest.fixture
def admin_membership(db, admin_user, tenant):
    return TenantMembership.objects.create(user=admin_user, tenant=tenant, role="admin")


@pytest.fixture
def member_membership(db, member_user, tenant):
    return TenantMembership.objects.create(user=member_user, tenant=tenant, role="member")


@pytest.mark.django_db
class TestListMembersView:
    url = "/api/v1/teams/members/"

    def test_unauthenticated_returns_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_member_without_tenant_context_returns_403(self, member_membership, member_user):
        client = auth_client(member_user)
        response = client.get(self.url)
        # Without tenant in request, IsTenantMember returns 403
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUpdateMemberRoleView:
    def url(self, pk):
        return f"/api/v1/teams/members/{pk}/"

    def test_unauthenticated_returns_401(self, member_membership):
        response = APIClient().patch(self.url(member_membership.pk), {"role": "admin"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_returns_403(self, member_membership, member_user):
        client = auth_client(member_user)
        response = client.patch(self.url(member_membership.pk), {"role": "admin"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRemoveMemberView:
    def url(self, pk):
        return f"/api/v1/teams/members/{pk}/remove/"

    def test_unauthenticated_returns_401(self, member_membership):
        response = APIClient().delete(self.url(member_membership.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_returns_403(self, member_membership, member_user):
        client = auth_client(member_user)
        response = client.delete(self.url(member_membership.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN
