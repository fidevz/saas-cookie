"""
Tests for invitation creation and acceptance flow.
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.teams.models import Invitation
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()

# Tenant slug is "teamcorp" → middleware resolves from this host
TENANT_HOST = "teamcorp.localhost"
TEAMS_OFF = {"FEATURE_FLAGS": {"TEAMS": False, "BILLING": True, "NOTIFICATIONS": True}}


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
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

    def test_accept_creates_correct_role(self, invitation, invitee_user):
        """The accepted membership must have the role specified in the invitation."""
        client = auth_client(invitee_user)
        client.post(self._accept_url(invitation.token))
        membership = TenantMembership.objects.get(user=invitee_user, tenant=invitation.tenant)
        assert membership.role == invitation.role

    def test_accept_sets_accepted_at_timestamp(self, invitation, invitee_user):
        client = auth_client(invitee_user)
        client.post(self._accept_url(invitation.token))
        invitation.refresh_from_db()
        assert invitation.accepted_at is not None


# ---------------------------------------------------------------------------
# POST /api/v1/teams/invitations/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInviteMemberView:
    url = "/api/v1/teams/invitations/"

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_admin_can_invite_new_member(self, mock_delay, admin_user, tenant):
        client = auth_client(admin_user)
        response = client.post(
            self.url,
            {"email": "newperson@example.com", "role": "member"},
            HTTP_HOST=TENANT_HOST,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Invitation.objects.filter(email="newperson@example.com", tenant=tenant).exists()
        mock_delay.assert_called_once()

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_invite_sends_email_task(self, mock_delay, admin_user, tenant):
        """Invitation creation must enqueue the email task."""
        client = auth_client(admin_user)
        client.post(
            self.url,
            {"email": "task@example.com", "role": "member"},
            HTTP_HOST=TENANT_HOST,
        )
        assert mock_delay.called
        invitation = Invitation.objects.get(email="task@example.com")
        mock_delay.assert_called_with(invitation.pk)

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_invite_already_member_returns_400(self, mock_delay, admin_user, invitee_user, tenant):
        TenantMembership.objects.create(user=invitee_user, tenant=tenant, role="member")
        client = auth_client(admin_user)
        response = client.post(
            self.url,
            {"email": invitee_user.email, "role": "member"},
            HTTP_HOST=TENANT_HOST,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_delay.assert_not_called()

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_reinvite_replaces_pending_invitation(self, mock_delay, admin_user, tenant):
        """Sending a second invite to the same email cancels the first."""
        Invitation.objects.create(
            email="pending@example.com",
            tenant=tenant,
            role="member",
            invited_by=admin_user,
            expires_at=timezone.now() + timedelta(hours=48),
        )
        client = auth_client(admin_user)
        client.post(
            self.url,
            {"email": "pending@example.com", "role": "admin"},
            HTTP_HOST=TENANT_HOST,
        )
        # Only the new invitation should exist
        invitations = Invitation.objects.filter(email="pending@example.com", tenant=tenant)
        assert invitations.count() == 1
        assert invitations.first().role == "admin"

    @override_settings(**TEAMS_OFF)
    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_feature_disabled_returns_403(self, mock_delay, admin_user, tenant):
        client = auth_client(admin_user)
        response = client.post(
            self.url,
            {"email": "x@example.com", "role": "member"},
            HTTP_HOST=TENANT_HOST,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_delay.assert_not_called()

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_member_cannot_invite(self, mock_delay, admin_user, invitee_user, tenant):
        TenantMembership.objects.create(user=invitee_user, tenant=tenant, role="member")
        client = auth_client(invitee_user)
        response = client.post(
            self.url,
            {"email": "other@example.com", "role": "member"},
            HTTP_HOST=TENANT_HOST,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_delay.assert_not_called()

    def test_unauthenticated_returns_401(self):
        response = APIClient().post(self.url, {"email": "x@example.com", "role": "member"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("apps.teams.tasks.send_invitation_email.delay")
    def test_no_tenant_context_returns_403(self, mock_delay, admin_user, tenant):
        """Without subdomain, IsTenantAdmin denies the request."""
        client = auth_client(admin_user)
        response = client.post(self.url, {"email": "x@example.com", "role": "member"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_delay.assert_not_called()
