"""
Tests for AuditLog model, log_action() helper, instrumented actions, and cleanup task.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.core.tasks import cleanup_old_audit_logs
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@audit.com", password="pass123")


@pytest.fixture
def member_user(db):
    return User.objects.create_user(email="member@audit.com", password="pass123")


@pytest.fixture
def tenant(db, owner):
    return Tenant.objects.create(name="AuditCo", slug="auditco", owner=owner)


@pytest.fixture
def admin_membership(db, owner, tenant):
    return TenantMembership.objects.create(
        user=owner, tenant=tenant, role=TenantMembership.Role.ADMIN
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAuditLogModel:
    def test_create_with_tenant(self, owner, tenant):
        log = AuditLog.objects.create(
            actor=owner,
            action="test.action",
            target="test-target",
            metadata={"key": "value"},
            tenant=tenant,
        )
        assert log.pk is not None
        assert log.tenant == tenant
        assert log.actor == owner
        assert log.action == "test.action"

    def test_create_without_tenant(self, owner):
        log = AuditLog.objects.create(actor=owner, action="system.action")
        assert log.pk is not None
        assert log.tenant is None

    def test_create_without_actor(self, tenant):
        log = AuditLog.objects.create(
            actor=None, action="webhook.action", tenant=tenant
        )
        assert log.pk is not None
        assert log.actor is None

    def test_str_representation(self, owner, tenant):
        log = AuditLog.objects.create(
            actor=owner, action="test.action", target="foo", tenant=tenant
        )
        s = str(log)
        assert "test.action" in s
        assert "foo" in s


# ---------------------------------------------------------------------------
# log_action() helper tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLogAction:
    def test_creates_entry_with_tenant(self, owner, tenant):
        from utils.audit import log_action

        log_action(
            actor=owner,
            action="user.invited",
            target="someone@example.com",
            metadata={"role": "member"},
            tenant=tenant,
        )
        log = AuditLog.objects.get(action="user.invited")
        assert log.actor == owner
        assert log.target == "someone@example.com"
        assert log.metadata == {"role": "member"}
        assert log.tenant == tenant

    def test_creates_entry_without_tenant(self, owner):
        from utils.audit import log_action

        log_action(actor=owner, action="system.event")
        log = AuditLog.objects.get(action="system.event")
        assert log.tenant is None

    def test_does_not_raise_on_db_failure(self, owner, tenant):
        from utils.audit import log_action

        with patch(
            "apps.core.models.AuditLog.objects.create", side_effect=Exception("DB down")
        ):
            # Should not raise — failures are swallowed and logged
            log_action(actor=owner, action="some.action", tenant=tenant)


# ---------------------------------------------------------------------------
# Integration: teams actions
# ---------------------------------------------------------------------------


INVITE_URL = "/api/v1/teams/invitations/"
ACCEPT_INVITE_URL = "/api/v1/teams/accept-invite/{}/"
CANCEL_INVITE_URL = "/api/v1/teams/invitations/{}/cancel/"
MEMBERS_URL = "/api/v1/teams/members/"
REMOVE_MEMBER_URL = "/api/v1/teams/members/{}/remove/"


def _auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestTeamsAuditLogs:
    def test_user_invited_logs_action(self, owner, tenant, admin_membership):
        client = _auth_client(owner)
        with patch("apps.teams.tasks.send_invitation_email") as mock_task:
            mock_task.delay.return_value = None
            resp = client.post(
                INVITE_URL,
                {"email": "new@audit.com", "role": "member"},
                HTTP_HOST=f"{tenant.slug}.localhost",
            )
        assert resp.status_code == 201
        log = AuditLog.objects.get(action="user.invited")
        assert log.tenant == tenant
        assert log.actor == owner
        assert log.target == "new@audit.com"
        assert log.metadata["role"] == "member"

    def test_invitation_cancelled_logs_action(self, owner, tenant, admin_membership):
        from apps.teams.models import Invitation

        inv = Invitation.objects.create(
            email="cancel@audit.com", tenant=tenant, role="member", invited_by=owner
        )
        client = _auth_client(owner)
        resp = client.delete(
            CANCEL_INVITE_URL.format(inv.pk),
            HTTP_HOST=f"{tenant.slug}.localhost",
        )
        assert resp.status_code == 204
        log = AuditLog.objects.get(action="invitation.cancelled")
        assert log.tenant == tenant
        assert log.actor == owner
        assert log.target == "cancel@audit.com"

    def test_invitation_accepted_logs_action(
        self, owner, tenant, admin_membership, member_user
    ):
        from apps.teams.models import Invitation

        inv = Invitation.objects.create(
            email=member_user.email, tenant=tenant, role="member", invited_by=owner
        )
        client = _auth_client(member_user)
        resp = client.post(
            ACCEPT_INVITE_URL.format(inv.token),
        )
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="invitation.accepted")
        assert log.tenant == tenant
        assert log.actor == member_user

    def test_member_removed_logs_action(
        self, owner, tenant, admin_membership, member_user
    ):
        membership = TenantMembership.objects.create(
            user=member_user, tenant=tenant, role=TenantMembership.Role.MEMBER
        )
        client = _auth_client(owner)
        resp = client.delete(
            REMOVE_MEMBER_URL.format(membership.pk),
            HTTP_HOST=f"{tenant.slug}.localhost",
        )
        assert resp.status_code == 204
        log = AuditLog.objects.get(action="member.removed")
        assert log.tenant == tenant
        assert log.actor == owner
        assert log.target == member_user.email


# ---------------------------------------------------------------------------
# Integration: subscription actions
# ---------------------------------------------------------------------------


SELECT_FREE_URL = "/api/v1/subscriptions/select-free/"
CANCEL_SUB_URL = "/api/v1/subscriptions/cancel/"


@pytest.mark.django_db
class TestSubscriptionsAuditLogs:
    def test_subscription_acquired_free_plan(self, owner, tenant, admin_membership):
        from apps.subscriptions.models import Plan

        Plan.objects.create(name="Free", amount=0, interval="month", is_active=True)
        client = _auth_client(owner)
        resp = client.post(SELECT_FREE_URL, HTTP_HOST=f"{tenant.slug}.localhost")
        assert resp.status_code == 201
        log = AuditLog.objects.get(action="subscription.acquired")
        assert log.tenant == tenant
        assert log.actor == owner
        assert log.metadata["source"] == "free_plan_selection"

    def test_subscription_cancelled_user_request(self, owner, tenant, admin_membership):
        from apps.subscriptions.models import Plan, Subscription

        plan = Plan.objects.create(
            name="Pro",
            stripe_price_id="price_x",
            amount=29,
            interval="month",
            is_active=True,
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_audit123",
            stripe_customer_id="cus_audit123",
        )
        client = _auth_client(owner)
        with patch("apps.subscriptions.views.stripe.Subscription.modify"):
            resp = client.post(CANCEL_SUB_URL, HTTP_HOST=f"{tenant.slug}.localhost")
        assert resp.status_code == 200
        log = AuditLog.objects.get(
            action="subscription.cancelled", metadata__source="user_request"
        )
        assert log.tenant == tenant
        assert log.actor == owner

    def test_subscription_acquired_via_webhook(self, owner, tenant):
        from apps.subscriptions.models import Plan
        from apps.subscriptions.webhooks import _handle_checkout_completed

        plan = Plan.objects.create(
            name="Pro",
            stripe_price_id="price_y",
            amount=29,
            interval="month",
            is_active=True,
        )
        session = {
            "subscription": "sub_wh001",
            "customer": "cus_wh001",
            "client_reference_id": str(tenant.pk),
            "metadata": {"plan_id": str(plan.pk)},
        }
        with patch("stripe.Subscription.retrieve") as mock_retrieve:
            mock_retrieve.return_value = {"items": {"data": []}, "trial_end": None}
            _handle_checkout_completed(session)

        log = AuditLog.objects.get(
            action="subscription.acquired", metadata__source="stripe_webhook"
        )
        assert log.tenant == tenant
        assert log.actor is None

    def test_subscription_upgraded_via_webhook(self, owner, tenant):
        from apps.subscriptions.models import Plan, Subscription
        from apps.subscriptions.webhooks import _handle_subscription_updated

        plan = Plan.objects.create(
            name="Pro",
            stripe_price_id="price_z",
            amount=29,
            interval="month",
            is_active=True,
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_upd001",
            stripe_customer_id="cus_upd001",
        )
        stripe_sub = {
            "id": "sub_upd001",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": None,
            "current_period_end": None,
            "trial_end": None,
        }
        _handle_subscription_updated(stripe_sub)

        log = AuditLog.objects.get(action="subscription.upgraded")
        assert log.tenant == tenant
        assert log.actor is None
        assert log.metadata["source"] == "stripe_webhook"

    def test_subscription_cancelled_via_webhook(self, owner, tenant):
        from apps.subscriptions.models import Plan, Subscription
        from apps.subscriptions.webhooks import _handle_subscription_deleted

        plan = Plan.objects.create(
            name="Pro",
            stripe_price_id="price_del",
            amount=29,
            interval="month",
            is_active=True,
        )
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_del001",
            stripe_customer_id="cus_del001",
        )
        _handle_subscription_deleted({"id": "sub_del001"})

        log = AuditLog.objects.get(
            action="subscription.cancelled", metadata__source="stripe_webhook"
        )
        assert log.tenant == tenant
        assert log.actor is None


# ---------------------------------------------------------------------------
# Integration: auth events
# ---------------------------------------------------------------------------


REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
PASSWORD_RESET_URL = "/api/v1/auth/password-reset/"
PASSWORD_RESET_CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"


@pytest.mark.django_db
class TestAuthAuditLogs:
    def test_register_logs_action(self, db):
        client = APIClient()
        resp = client.post(
            REGISTER_URL,
            {
                "email": "register@audit.com",
                "password": "securepass123",
                "first_name": "Reg",
                "last_name": "User",
                "company_name": "RegCo",
                "slug": "reg-co",
            },
        )
        assert resp.status_code == 201
        log = AuditLog.objects.get(action="user.registered")
        assert log.target == "register@audit.com"
        assert log.metadata["method"] == "email"

    def test_login_logs_action(self, db):
        user = User.objects.create_user(
            email="loginaudit@audit.com", password="pass123"
        )
        from allauth.account.models import EmailAddress

        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        client = APIClient()
        resp = client.post(LOGIN_URL, {"email": user.email, "password": "pass123"})
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="user.login", metadata__method="email")
        assert log.actor == user
        assert log.target == user.email

    def test_login_failed_unverified_email_logs_action(self, db):
        user = User.objects.create_user(
            email="unverified@audit.com", password="pass123"
        )
        # No verified EmailAddress — login should fail with email_not_verified
        client = APIClient()
        resp = client.post(LOGIN_URL, {"email": user.email, "password": "pass123"})
        assert resp.status_code == 403
        log = AuditLog.objects.get(action="user.login_failed")
        assert log.target == user.email
        assert log.metadata["reason"] == "email_not_verified"

    def test_logout_logs_action(self, db):
        user = User.objects.create_user(email="logout@audit.com", password="pass123")
        from allauth.account.models import EmailAddress

        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        client = APIClient()
        client.post(LOGIN_URL, {"email": user.email, "password": "pass123"})
        client.force_authenticate(user=user)
        resp = client.post(LOGOUT_URL)
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="user.logout")
        assert log.actor == user

    def test_password_reset_requested_logs_action(self, db):
        user = User.objects.create_user(email="pwreset@audit.com", password="pass123")
        from allauth.account.models import EmailAddress

        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        client = APIClient()
        with patch("utils.email.send_email"):
            resp = client.post(PASSWORD_RESET_URL, {"email": user.email})
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="password.reset_requested")
        assert log.target == user.email

    def test_password_reset_completed_logs_action(self, db):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = User.objects.create_user(email="pwconfirm@audit.com", password="pass123")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        combined = f"{uid}-{token}"
        client = APIClient()
        resp = client.post(
            PASSWORD_RESET_CONFIRM_URL,
            {"token": combined, "new_password": "newSecurePass456!"},
        )
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="password.reset_completed")
        assert log.actor == user
        assert log.target == user.email


# ---------------------------------------------------------------------------
# Integration: user email change events
# ---------------------------------------------------------------------------


ME_EMAIL_URL = "/api/v1/users/me/email/"
ME_EMAIL_CONFIRM_URL = "/api/v1/users/me/email/confirm/"
ME_EMAIL_CANCEL_URL = "/api/v1/users/me/email/cancel/"


@pytest.mark.django_db
class TestUserAuditLogs:
    def test_email_change_requested_logs_action(self, owner):
        client = _auth_client(owner)
        with patch("apps.users.views.send_email"):
            resp = client.post(
                ME_EMAIL_URL, {"new_email": "new@audit.com", "password": "pass123"}
            )
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="email.change_requested")
        assert log.actor == owner
        assert log.metadata["new_email"] == "new@audit.com"

    def test_email_change_confirmed_logs_action(self, owner):
        from django.core import signing

        new_email = "confirmed@audit.com"
        owner.pending_email = new_email
        owner.save(update_fields=["pending_email"])
        token = signing.dumps(
            {"uid": owner.pk, "email": new_email}, salt="email-change"
        )
        client = APIClient()
        resp = client.post(ME_EMAIL_CONFIRM_URL, {"token": token})
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="email.changed")
        assert log.actor == owner
        assert log.metadata["new_email"] == new_email

    def test_email_change_cancelled_logs_action(self, owner):
        from django.core import signing

        pending = "cancel@audit.com"
        owner.pending_email = pending
        owner.save(update_fields=["pending_email"])
        token = signing.dumps({"uid": owner.pk, "email": pending}, salt="email-change")
        client = APIClient()
        resp = client.post(ME_EMAIL_CANCEL_URL, {"token": token})
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="email.change_cancelled")
        assert log.actor == owner


# ---------------------------------------------------------------------------
# Integration: role change
# ---------------------------------------------------------------------------


UPDATE_MEMBER_URL = "/api/v1/teams/members/{}/"


@pytest.mark.django_db
class TestRoleChangeAuditLog:
    def test_role_change_logs_action(
        self, owner, tenant, admin_membership, member_user
    ):
        membership = TenantMembership.objects.create(
            user=member_user, tenant=tenant, role=TenantMembership.Role.MEMBER
        )
        client = _auth_client(owner)
        resp = client.patch(
            UPDATE_MEMBER_URL.format(membership.pk),
            {"role": "admin"},
            HTTP_HOST=f"{tenant.slug}.localhost",
        )
        assert resp.status_code == 200
        log = AuditLog.objects.get(action="member.role_changed")
        assert log.actor == owner
        assert log.target == member_user.email
        assert log.metadata["old_role"] == TenantMembership.Role.MEMBER
        assert log.metadata["new_role"] == TenantMembership.Role.ADMIN


# ---------------------------------------------------------------------------
# Cleanup task tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCleanupOldAuditLogs:
    def test_deletes_old_logs(self, owner, tenant):
        old = AuditLog.objects.create(actor=owner, action="old.action", tenant=tenant)
        AuditLog.objects.filter(pk=old.pk).update(
            timestamp=timezone.now() - timezone.timedelta(days=91)
        )
        recent = AuditLog.objects.create(
            actor=owner, action="recent.action", tenant=tenant
        )

        cleanup_old_audit_logs(days=90)

        assert not AuditLog.objects.filter(pk=old.pk).exists()
        assert AuditLog.objects.filter(pk=recent.pk).exists()

    def test_keeps_logs_within_retention(self, owner, tenant):
        log = AuditLog.objects.create(actor=owner, action="keep.action", tenant=tenant)
        cleanup_old_audit_logs(days=90)
        assert AuditLog.objects.filter(pk=log.pk).exists()
