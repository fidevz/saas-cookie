"""
Tests for team views — focusing on plan limit enforcement in AcceptInviteView.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.subscriptions.capabilities import default_capabilities
from apps.subscriptions.models import Plan, Subscription
from apps.teams.models import Invitation
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def accept_url(token):
    return f"/api/v1/teams/accept-invite/{token}/"


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@team.com", password="pass123")


@pytest.fixture
def invitee(db):
    return User.objects.create_user(email="invitee@team.com", password="pass123")


@pytest.fixture
def tenant(db, admin_user):
    t = Tenant.objects.create(name="TeamCo", slug="teamco", owner=admin_user)
    TenantMembership.objects.create(
        user=admin_user, tenant=t, role=TenantMembership.Role.ADMIN
    )
    return t


@pytest.fixture
def plan_with_teams(db):
    caps = {**default_capabilities(), "teams": True, "team_members": 3}
    return Plan.objects.create(
        name="Pro",
        stripe_price_id="price_pro",
        amount="29.00",
        interval="month",
        capabilities=caps,
    )


@pytest.fixture
def plan_no_teams(db):
    caps = {**default_capabilities(), "teams": False, "team_members": 1}
    return Plan.objects.create(
        name="Free",
        stripe_price_id="price_free",
        amount="0.00",
        interval="month",
        capabilities=caps,
    )


@pytest.fixture
def subscription(db, tenant, plan_with_teams):
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan_with_teams,
        status=Subscription.Status.ACTIVE,
        stripe_subscription_id="sub_test",
        stripe_customer_id="cus_test",
        capabilities=plan_with_teams.capabilities,
    )


def make_invitation(tenant, email, admin_user):
    return Invitation.objects.create(
        tenant=tenant,
        email=email,
        role=TenantMembership.Role.MEMBER,
        invited_by=admin_user,
        expires_at=timezone.now() + timezone.timedelta(hours=48),
    )


@pytest.mark.django_db
class TestAcceptInviteViewLimits:
    def test_accept_succeeds_within_limit(
        self, invitee, tenant, admin_user, subscription
    ):
        # Current: 1 member (admin). Limit: 3. Should pass.
        invitation = make_invitation(tenant, invitee.email, admin_user)
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_200_OK
        assert TenantMembership.objects.filter(tenant=tenant, user=invitee).exists()

    def test_accept_blocked_when_at_limit(
        self, invitee, tenant, admin_user, plan_with_teams
    ):
        # Set limit to 1 — admin is already the 1 member.
        caps = {**default_capabilities(), "teams": True, "team_members": 1}
        Subscription.objects.create(
            tenant=tenant,
            plan=plan_with_teams,
            status=Subscription.Status.ACTIVE,
            capabilities=caps,
        )
        invitation = make_invitation(tenant, invitee.email, admin_user)
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Membership must NOT have been created
        assert not TenantMembership.objects.filter(tenant=tenant, user=invitee).exists()

    def test_accept_blocked_when_teams_capability_disabled(
        self, invitee, tenant, admin_user, plan_no_teams
    ):
        Subscription.objects.create(
            tenant=tenant,
            plan=plan_no_teams,
            status=Subscription.Status.ACTIVE,
            capabilities=plan_no_teams.capabilities,
        )
        invitation = make_invitation(tenant, invitee.email, admin_user)
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_accept_allowed_with_no_subscription(self, invitee, tenant, admin_user):
        # No subscription = no billing restrictions, accept should succeed.
        invitation = make_invitation(tenant, invitee.email, admin_user)
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_200_OK

    def test_accept_existing_member_skips_limit_check(
        self, invitee, tenant, admin_user, plan_with_teams
    ):
        # Invitee is already a member. Limit of 1 is exceeded but role update should still work.
        TenantMembership.objects.create(
            user=invitee, tenant=tenant, role=TenantMembership.Role.MEMBER
        )
        caps = {**default_capabilities(), "teams": True, "team_members": 1}
        Subscription.objects.create(
            tenant=tenant,
            plan=plan_with_teams,
            status=Subscription.Status.ACTIVE,
            capabilities=caps,
        )
        # Re-invite with admin role
        invitation = Invitation.objects.create(
            tenant=tenant,
            email=invitee.email,
            role=TenantMembership.Role.ADMIN,
            invited_by=admin_user,
            expires_at=timezone.now() + timezone.timedelta(hours=48),
        )
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_200_OK
        membership = TenantMembership.objects.get(user=invitee, tenant=tenant)
        assert membership.role == TenantMembership.Role.ADMIN

    def test_accept_unlimited_plan_always_passes(
        self, invitee, tenant, admin_user, plan_with_teams
    ):
        # team_members = None means unlimited
        caps = {**default_capabilities(), "teams": True, "team_members": None}
        Subscription.objects.create(
            tenant=tenant,
            plan=plan_with_teams,
            status=Subscription.Status.ACTIVE,
            capabilities=caps,
        )
        invitation = make_invitation(tenant, invitee.email, admin_user)
        response = auth_client(invitee).post(accept_url(invitation.token))
        assert response.status_code == status.HTTP_200_OK
