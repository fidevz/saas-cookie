"""
Authentication serializers.
"""
import logging
import re

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)

RESERVED_SLUGS = frozenset({
    "www", "api", "app", "admin", "mail", "static", "media",
    "dev", "staging", "prod", "help", "support", "blog", "status",
    "dashboard", "billing", "auth", "invite",
})


class RegisterSerializer(serializers.Serializer):
    """User registration — creates user + tenant, or joins via invite_token."""

    # Workspace fields — required only when not using an invite_token
    company_name = serializers.CharField(max_length=200, min_length=2, required=False, allow_blank=True)
    slug = serializers.RegexField(
        r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$",
        required=False,
        allow_blank=True,
        error_messages={
            "invalid": (
                "Slug must be 3–50 characters: lowercase letters, numbers, and hyphens only. "
                "Cannot start or end with a hyphen."
            )
        },
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    invite_token = serializers.CharField(required=False, write_only=True)

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
        return normalized

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate_slug(self, value: str) -> str:
        from apps.tenants.models import Tenant

        if value in RESERVED_SLUGS:
            raise serializers.ValidationError(_("That workspace URL is reserved."))
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError(_("That workspace URL is already taken."))
        return value

    def validate(self, attrs: dict) -> dict:
        invite_token = attrs.get("invite_token")
        if invite_token:
            from apps.teams.models import Invitation
            try:
                invitation = Invitation.objects.select_related("tenant").get(token=invite_token)
            except (Invitation.DoesNotExist, ValueError):
                raise serializers.ValidationError({"invite_token": _("Invalid invitation token.")})
            if not invitation.is_valid:
                raise serializers.ValidationError({"invite_token": _("This invitation has expired or already been used.")})
            attrs["_invitation"] = invitation
        else:
            if not attrs.get("company_name"):
                raise serializers.ValidationError({"company_name": _("This field is required.")})
            if not attrs.get("slug"):
                raise serializers.ValidationError({"slug": _("This field is required.")})
        return attrs

    def create(self, validated_data: dict) -> tuple:
        from apps.tenants.models import Tenant, TenantMembership

        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "").strip()
        last_name = validated_data.get("last_name", "").strip()
        invitation = validated_data.pop("_invitation", None)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if invitation:
            # Join existing tenant via invitation
            TenantMembership.objects.get_or_create(
                user=user,
                tenant=invitation.tenant,
                defaults={"role": invitation.role},
            )
            invitation.accepted = True
            from django.utils import timezone
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["accepted", "accepted_at"])
            tenant = invitation.tenant
        else:
            # Create new tenant
            company_name = validated_data["company_name"].strip()
            slug = validated_data["slug"]
            tenant = Tenant.objects.create(name=company_name, slug=slug, owner=user)
            TenantMembership.objects.create(
                user=user, tenant=tenant, role=TenantMembership.Role.ADMIN,
            )

        # Invited users have already verified their email by clicking the link
        from allauth.account.models import EmailAddress
        request = self.context.get("request")
        if invitation:
            EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
        else:
            ea = EmailAddress.objects.create(user=user, email=email, primary=True, verified=False)
            ea.send_confirmation(request, signup=True)

        logger.info("New user registered: %s (tenant: %s)", email, tenant.slug)
        return user, tenant


class LoginSerializer(serializers.Serializer):
    """Authenticate with email + password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                _("Unable to log in with provided credentials."),
                code="authorization",
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("User account is disabled."),
                code="authorization",
            )

        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password-reset email."""

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm a password reset with token + new password."""

    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value
