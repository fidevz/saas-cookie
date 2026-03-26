"""
Tests for member listing, role update, and removal.

Tenant context is injected via the Host header (e.g. "membercorp.localhost").
The TenantMiddleware resolves the slug from the subdomain, which is the same
path the real application takes — no monkey-patching required.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()

# dev settings allow *.localhost — middleware resolves "membercorp" from this host
TENANT_HOST = "membercorp.localhost"
TEAMS_OFF = {"FEATURE_FLAGS": {"TEAMS": False, "BILLING": True, "NOTIFICATIONS": True}}


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
    return User.objects.create_user(
        email="member@members.com", password="memberpass123"
    )


@pytest.fixture
def tenant(db, admin_user):
    return Tenant.objects.create(name="MemberCorp", slug="membercorp", owner=admin_user)


@pytest.fixture
def admin_membership(db, admin_user, tenant):
    return TenantMembership.objects.create(user=admin_user, tenant=tenant, role="admin")


@pytest.fixture
def member_membership(db, member_user, tenant):
    return TenantMembership.objects.create(
        user=member_user, tenant=tenant, role="member"
    )


# ---------------------------------------------------------------------------
# GET /api/v1/teams/members/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListMembersView:
    url = "/api/v1/teams/members/"

    def test_admin_can_list_members(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        response = client.get(self.url, HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_member_can_list_members(
        self, admin_membership, member_membership, member_user
    ):
        """Regular members (not admins) also have read access to the member list."""
        client = auth_client(member_user)
        response = client.get(self.url, HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_response_includes_user_details(self, admin_membership, admin_user):
        client = auth_client(admin_user)
        response = client.get(self.url, HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_200_OK
        result = response.data["results"][0]
        assert "role" in result
        assert "user" in result

    def test_only_current_tenant_members_returned(
        self, admin_membership, member_membership, admin_user, db
    ):
        """Members of another tenant must not bleed into this tenant's list."""
        other_user = User.objects.create_user(
            email="other@example.com", password="pass"
        )
        other_tenant = Tenant.objects.create(
            name="Other Corp", slug="othercorp", owner=other_user
        )
        TenantMembership.objects.create(
            user=other_user, tenant=other_tenant, role="admin"
        )

        client = auth_client(admin_user)
        response = client.get(self.url, HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # only membercorp members

    @override_settings(**TEAMS_OFF)
    def test_feature_disabled_returns_403(self, admin_membership, admin_user):
        client = auth_client(admin_user)
        response = client.get(self.url, HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_tenant_context_returns_403(self, admin_membership, admin_user):
        """Without a subdomain, middleware sets tenant=None → IsTenantMember denies."""
        client = auth_client(admin_user)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# PATCH /api/v1/teams/members/{id}/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateMemberRoleView:
    def url(self, pk):
        return f"/api/v1/teams/members/{pk}/"

    def test_admin_can_promote_member_to_admin(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        response = client.patch(
            self.url(member_membership.pk), {"role": "admin"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_200_OK
        member_membership.refresh_from_db()
        assert member_membership.role == TenantMembership.Role.ADMIN

    def test_admin_can_demote_when_multiple_admins_exist(
        self, admin_membership, member_membership, admin_user
    ):
        """Demotion is allowed as long as at least one admin remains."""
        member_membership.role = TenantMembership.Role.ADMIN
        member_membership.save()

        client = auth_client(admin_user)
        response = client.patch(
            self.url(member_membership.pk), {"role": "member"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_200_OK
        member_membership.refresh_from_db()
        assert member_membership.role == TenantMembership.Role.MEMBER

    def test_cannot_demote_last_admin(self, admin_membership, admin_user):
        """Demoting the only admin must return 400."""
        client = auth_client(admin_user)
        response = client.patch(
            self.url(admin_membership.pk), {"role": "member"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_role_unchanged_after_failed_demote(self, admin_membership, admin_user):
        """DB must not be mutated when the guard fires."""
        client = auth_client(admin_user)
        client.patch(
            self.url(admin_membership.pk), {"role": "member"}, HTTP_HOST=TENANT_HOST
        )
        admin_membership.refresh_from_db()
        assert admin_membership.role == TenantMembership.Role.ADMIN

    def test_member_cannot_update_role(
        self, admin_membership, member_membership, member_user
    ):
        client = auth_client(member_user)
        response = client.patch(
            self.url(member_membership.pk), {"role": "admin"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_membership_from_other_tenant_returns_404(
        self, admin_membership, admin_user, db
    ):
        """Admins cannot mutate memberships that belong to a different tenant."""
        other_user = User.objects.create_user(
            email="other@example.com", password="pass"
        )
        other_tenant = Tenant.objects.create(
            name="Other", slug="othertenant", owner=other_user
        )
        other_membership = TenantMembership.objects.create(
            user=other_user, tenant=other_tenant, role="admin"
        )

        client = auth_client(admin_user)
        response = client.patch(
            self.url(other_membership.pk), {"role": "member"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(**TEAMS_OFF)
    def test_feature_disabled_returns_403(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        response = client.patch(
            self.url(member_membership.pk), {"role": "admin"}, HTTP_HOST=TENANT_HOST
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, member_membership):
        response = APIClient().patch(self.url(member_membership.pk), {"role": "admin"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_tenant_context_returns_403(
        self, admin_membership, admin_user, member_membership
    ):
        client = auth_client(admin_user)
        response = client.patch(self.url(member_membership.pk), {"role": "admin"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# DELETE /api/v1/teams/members/{id}/remove/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRemoveMemberView:
    def url(self, pk):
        return f"/api/v1/teams/members/{pk}/remove/"

    def test_admin_can_remove_member(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        response = client.delete(self.url(member_membership.pk), HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TenantMembership.objects.filter(pk=member_membership.pk).exists()

    def test_removed_member_count_decreases(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        client.delete(self.url(member_membership.pk), HTTP_HOST=TENANT_HOST)
        assert (
            TenantMembership.objects.filter(tenant=admin_membership.tenant).count() == 1
        )

    def test_cannot_remove_self(self, admin_membership, admin_user):
        client = auth_client(admin_user)
        response = client.delete(self.url(admin_membership.pk), HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_membership_from_other_tenant_returns_404(
        self, admin_membership, admin_user, db
    ):
        """Admins cannot remove memberships from a different tenant."""
        other_user = User.objects.create_user(
            email="other@example.com", password="pass"
        )
        other_tenant = Tenant.objects.create(
            name="Other", slug="othertenant", owner=other_user
        )
        other_membership = TenantMembership.objects.create(
            user=other_user, tenant=other_tenant, role="member"
        )

        client = auth_client(admin_user)
        response = client.delete(self.url(other_membership.pk), HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_member_cannot_remove_others(
        self, admin_membership, member_membership, member_user
    ):
        client = auth_client(member_user)
        response = client.delete(self.url(admin_membership.pk), HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(**TEAMS_OFF)
    def test_feature_disabled_returns_403(
        self, admin_membership, member_membership, admin_user
    ):
        client = auth_client(admin_user)
        response = client.delete(self.url(member_membership.pk), HTTP_HOST=TENANT_HOST)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, member_membership):
        response = APIClient().delete(self.url(member_membership.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_tenant_context_returns_403(
        self, admin_membership, admin_user, member_membership
    ):
        client = auth_client(admin_user)
        response = client.delete(self.url(member_membership.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN
