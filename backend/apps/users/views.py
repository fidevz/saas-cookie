"""
User profile views.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import CustomUser
from apps.users.serializers import UserProfileSerializer
from utils.audit import log_action
from utils.email import send_email
from utils.throttling import EmailChangeThrottle

User = get_user_model()
logger = logging.getLogger(__name__)

EMAIL_CHANGE_SALT = "email-change"
EMAIL_CHANGE_MAX_AGE = 86400  # 24 hours


class ProfileView(RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/users/me/ — retrieve or update the authenticated user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self) -> CustomUser:
        return self.request.user


def _get_site_context(request):
    app_name = getattr(settings, "APP_NAME", "App")
    try:
        from django.contrib.sites.models import Site

        current_site = Site.objects.get_current(request)
    except Exception:
        current_site = type(
            "_Site", (), {"name": app_name, "domain": settings.BASE_DOMAIN}
        )()
    return current_site


class EmailChangeRequestView(APIView):
    """POST /api/v1/users/me/email/ — initiate an email change."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailChangeThrottle]

    def post(self, request: Request) -> Response:
        user = request.user
        new_email = request.data.get("new_email", "").strip().lower()
        password = request.data.get("password", "")

        if not new_email:
            return Response(
                {"detail": "new_email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not password:
            return Response(
                {"detail": "password is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_email == user.email:
            return Response(
                {"detail": "New email must be different from your current email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=new_email).exists():
            return Response(
                {"detail": "That email address is already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = signing.dumps(
            {"uid": user.pk, "email": new_email}, salt=EMAIL_CHANGE_SALT
        )

        user.pending_email = new_email
        user.save(update_fields=["pending_email"])

        # Use the request Origin so the link goes to the correct tenant subdomain,
        # not the generic FRONTEND_URL (which is the root domain).
        frontend_url = request.META.get("HTTP_ORIGIN") or getattr(
            settings, "FRONTEND_URL", "http://localhost:3000"
        )
        app_name = getattr(settings, "APP_NAME", "App")
        current_site = _get_site_context(request)

        confirm_url = f"{frontend_url}/settings/confirm-email?token={token}"
        cancel_url = f"{frontend_url}/settings/cancel-email-change?token={token}"

        context = {
            "user": user,
            "new_email": new_email,
            "confirm_url": confirm_url,
            "cancel_url": cancel_url,
            "current_site": current_site,
        }

        # Email 1: confirmation link → new address
        html_body = render_to_string(
            "account/email/email_change_confirm_message.html", context
        )
        text_body = render_to_string(
            "account/email/email_change_confirm_message.txt", context
        )
        send_email(
            to=new_email,
            subject=f"Confirm your new email — {app_name}",
            html_body=html_body,
            text_body=text_body,
        )

        # Email 2: alert + cancel link → old address
        html_body = render_to_string(
            "account/email/email_change_notify_message.html", context
        )
        text_body = render_to_string(
            "account/email/email_change_notify_message.txt", context
        )
        send_email(
            to=user.email,
            subject=f"Your email address is being changed — {app_name}",
            html_body=html_body,
            text_body=text_body,
        )

        logger.info("Email change initiated for user %s → %s", user.pk, new_email)
        log_action(
            actor=user,
            action="email.change_requested",
            target=user.email,
            metadata={"new_email": new_email},
        )
        return Response({"detail": f"Verification email sent to {new_email}."})


class EmailChangeConfirmView(APIView):
    """POST /api/v1/users/me/email/confirm/ — confirm email change via signed token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token = request.data.get("token", "").strip()
        if not token:
            return Response(
                {"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = signing.loads(
                token, salt=EMAIL_CHANGE_SALT, max_age=EMAIL_CHANGE_MAX_AGE
            )
        except signing.SignatureExpired:
            return Response(
                {"detail": "This link has expired. Please request a new email change."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid or tampered token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=data["uid"])
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )

        new_email = data["email"]

        if user.pending_email != new_email:
            return Response(
                {
                    "detail": "This email change request has already been used or cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            user.pending_email = ""
            user.save(update_fields=["pending_email"])
            return Response(
                {
                    "detail": "That email address is already in use. Please request a new email change."
                },
                status=status.HTTP_409_CONFLICT,
            )

        old_email = user.email
        user.email = new_email
        user.pending_email = ""
        user.save(update_fields=["email", "pending_email"])

        # Update allauth EmailAddress records
        from allauth.account.models import EmailAddress

        EmailAddress.objects.filter(user=user, email=old_email).update(
            email=new_email, verified=True, primary=True
        )
        if not EmailAddress.objects.filter(user=user, email=new_email).exists():
            EmailAddress.objects.create(
                user=user, email=new_email, verified=True, primary=True
            )

        # Blacklist all outstanding refresh tokens, then issue a fresh pair
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        from rest_framework_simplejwt.tokens import RefreshToken as RT

        for token_obj in OutstandingToken.objects.filter(user=user):
            try:
                RT(token_obj.token).blacklist()
            except Exception:
                pass

        refresh = RT.for_user(user)
        access = str(refresh.access_token)

        from apps.users.serializers import UserSerializer

        user_data = UserSerializer(user).data

        logger.info("Email changed for user %s: %s → %s", user.pk, old_email, new_email)
        log_action(
            actor=user,
            action="email.changed",
            target=new_email,
            metadata={"old_email": old_email, "new_email": new_email},
        )

        from apps.core.features import FeatureFlags

        if FeatureFlags.billing_enabled():
            from apps.subscriptions.tasks import sync_stripe_customer_email

            sync_stripe_customer_email.delay(user.pk, new_email)

        response = Response(
            {
                "detail": "Email updated successfully.",
                "access": access,
                "user": user_data,
            }
        )
        from apps.authentication.views import _set_refresh_cookie

        _set_refresh_cookie(response, refresh)
        return response


class EmailChangeCancelView(APIView):
    """POST /api/v1/users/me/email/cancel/ — cancel a pending email change."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token = request.data.get("token", "").strip()
        if not token:
            return Response(
                {"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = signing.loads(
                token, salt=EMAIL_CHANGE_SALT, max_age=EMAIL_CHANGE_MAX_AGE
            )
        except signing.SignatureExpired:
            return Response(
                {"detail": "This link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid or tampered token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=data["uid"])
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )

        if user.pending_email == data["email"]:
            user.pending_email = ""
            user.save(update_fields=["pending_email"])
            logger.info("Email change cancelled for user %s", user.pk)
            log_action(
                actor=user,
                action="email.change_cancelled",
                target=user.email,
                metadata={"cancelled_email": data["email"]},
            )

        return Response({"detail": "Email change cancelled."})
