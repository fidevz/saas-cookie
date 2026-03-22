"""
Tests for invitation creation and acceptance flow.
"""
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.teams.models import Invitation
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def with_tenant(client, tenant):
    """Attach tenant to the WSGI environ so middleware sets it."""
    client._tenant = tenant
    return client


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@teams.com", password="adminpass123")


@pytest.fixture
def invitee_user(db):
    return User.objects.create_user(email="invitee@teams.com", password="pass123")


@pytest.fixture
def tenant(db, admin_user):
    t = Tenant.objects.create(name="TeamCorp", slug="teamcorp", owner=admin_user)
    TenantMembership.objects.create(user=admin_user, tenant=t, role="admin")
    return t


@pytest.fixture
def invitation(db, tenant, admin_user):
    return Invitation.objects.create(
        email="invitee@teams.com",
        tenant=tenant,
        role="member",
        invited_by=admin_user,
        expires_at=timezone.now() + timedelta(hours=48),
    )


@pytest.mark.django_db
class TestInvitationModel:
    def test_is_valid_for_pending_unexpired(self, invitation):
        assert invitation.is_valid is True

    def test_is_expired_for_past_expiry(self, invitation):
        invitation.expires_at = timezone.now() - timedelta(hours=1)
        assert invitation.is_expired is True

    def test_is_invalid_when_accepted(self, invitation):
        invitation.accepted = True
        assert invitation.is_valid is False

    def test_token_is_uuid(self, invitation):
        assert isinstance(invitation.token, uuid.UUID)

    def test_str_representation(self, invitation):
        assert "invitee@teams.com" in str(invitation)


@pytest.mark.django_db
class TestAcceptInviteView:
    def _accept_url(self, token):
        return f"/api/v1/teams/accept-invite/{token}/"

    def test_accept_valid_invitation(self, invitation, invitee_user):
        client = auth_client(invitee_user)
        response = client.post(self._accept_url(invitation.token))
        assert response.status_code == status.HTTP_200_OK
        invitation.refresh_from_db()
        assert invitation.accepted is True
        assert TenantMembership.objects.filter(
            user=invitee_user, tenant=invitation.tenant
        ).exists()

    def test_accept_unauthenticated_returns_401(self, invitation):
        client = APIClient()
        response = client.post(self._accept_url(invitation.token))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_accept_wrong_email_returns_403(self, invitation, admin_user):
        client = auth_client(admin_user)
        response = client.post(self._accept_url(invitation.token))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_accept_expired_invitation(self, invitation, invitee_user):
        invitation.expires_at = timezone.now() - timedelta(hours=1)
        invitation.save()
        client = auth_client(invitee_user)
        response = client.post(self._accept_url(invitation.token))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_already_accepted_invitation(self, invitation, invitee_user):
        invitation.accepted = True
        invitation.save()
        client = auth_client(invitee_user)
        response = client.post(self._accept_url(invitation.token))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_nonexistent_token(self, invitee_user):
        client = auth_client(invitee_user)
        response = client.post(self._accept_url(uuid.uuid4()))
        assert response.status_code == status.HTTP_404_NOT_FOUND
