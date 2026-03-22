"""
Authentication serializers.
"""
import logging

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.Serializer):
    """User registration — creates user, tenant, and admin membership."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
        return normalized

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict) -> User:
        # Import here to avoid circular imports
        from apps.tenants.models import Tenant, TenantMembership
        import re

        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "").strip()
        last_name = validated_data.get("last_name", "").strip()

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Auto-create a tenant for the new user
        base_slug = re.sub(r"[^a-z0-9]+", "-", email.split("@")[0].lower()).strip("-")
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant.objects.create(
            name=first_name or email.split("@")[0],
            slug=slug,
            owner=user,
        )

        TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role=TenantMembership.Role.ADMIN,
        )

        logger.info("New user registered: %s (tenant: %s)", email, slug)
        return user


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
