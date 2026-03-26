"""
Authentication views: register, login, logout, token refresh, Google OAuth,
password reset, email verification.
"""
import logging
import secrets

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from utils.throttling import LoginThrottle, RegisterThrottle, ResendVerificationThrottle

User = get_user_model()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
COOKIE_SETTINGS = {
    "key": settings.SIMPLE_JWT.get("AUTH_COOKIE", "refresh_token"),
    "path": settings.SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/"),
    "domain": settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN"),
    "secure": settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", True),
    "httponly": settings.SIMPLE_JWT.get("AUTH_COOKIE_HTTP_ONLY", True),
    "samesite": settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
}


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = int(
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    )
    response.set_cookie(
        max_age=max_age,
        value=str(refresh_token),
        **COOKIE_SETTINGS,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_SETTINGS["key"],
        path=COOKIE_SETTINGS["path"],
        domain=COOKIE_SETTINGS["domain"],
        samesite=COOKIE_SETTINGS["samesite"],
    )


def _tokens_for_user(user) -> tuple[str, RefreshToken]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), refresh


def _generate_login_code(user_id: int) -> str:
    """Store a single-use, 60-second opaque code in Redis and return it."""
    code = secrets.token_urlsafe(32)
    cache.set(f"login_code:{code}", user_id, timeout=60)
    return code


def _tenant_slug_for_user(user) -> str | None:
    from apps.tenants.models import TenantMembership
    membership = (
        TenantMembership.objects.select_related("tenant").filter(user=user).first()
    )
    return membership.tenant.slug if membership else None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — create account + tenant."""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user, tenant = serializer.save()

        access, refresh = _tokens_for_user(user)

        response = Response(
            {
                "access": access,
                "tenant_slug": tenant.slug,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )
        _set_refresh_cookie(response, refresh)
        return response


class LoginView(APIView):
    """POST /api/v1/auth/login/ — authenticate and receive tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Check email verification before issuing tokens.
        # Google OAuth users are always verified (allauth marks them automatically).
        from allauth.account.models import EmailAddress
        if not EmailAddress.objects.filter(user=user, verified=True).exists():
            return Response(
                {
                    "code": "email_not_verified",
                    "detail": "Please verify your email address before signing in.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Fire the standard Django login signal so connected handlers
        # (e.g. welcome notification) are triggered, and last_login is updated.
        from django.contrib.auth.signals import user_logged_in
        user_logged_in.send(sender=user.__class__, request=request, user=user)

        # Refresh to pick up any changes made by signal handlers (e.g. is_first_login).
        user.refresh_from_db()

        # Resolve tenant for this user (first admin membership)
        from apps.tenants.models import TenantMembership
        membership = (
            TenantMembership.objects.select_related("tenant")
            .filter(user=user)
            .first()
        )
        tenant_slug = membership.tenant.slug if membership else None

        access, refresh = _tokens_for_user(user)

        response = Response(
            {
                "access": access,
                "tenant_slug": tenant_slug,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_first_login": user.is_first_login,
                },
            }
        )
        _set_refresh_cookie(response, refresh)
        return response


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh token + clear cookie."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get(COOKIE_SETTINGS["key"])
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # Already invalid — that's fine

        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        _clear_refresh_cookie(response)
        return response


class TokenRefreshCookieView(APIView):
    """POST /api/v1/auth/token/refresh/ — exchange httpOnly cookie for new access token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get(COOKIE_SETTINGS["key"])
        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            access = str(token.access_token)
        except (TokenError, InvalidToken) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"access": access})

        # If rotation is enabled, a new refresh token was generated — update the cookie
        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):
            _set_refresh_cookie(response, token)

        return response


class ResendVerificationView(APIView):
    """POST /api/v1/auth/resend-verification/ — resend email confirmation link."""

    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationThrottle]

    def post(self, request: Request) -> Response:
        email = request.data.get("email", "").strip().lower()

        if email:
            from allauth.account.models import EmailAddress

            ea = EmailAddress.objects.filter(email=email, verified=False).first()
            if ea:
                try:
                    ea.send_confirmation(request, signup=False)
                except Exception:
                    logger.exception("Failed to resend verification email to %s", email)

        # Always 200 — never reveal whether an email exists
        return Response(
            {"detail": "If that email exists and is unverified, a new confirmation link was sent."}
        )


class VerifyEmailView(APIView):
    """POST /api/v1/auth/verify-email/ — confirm email address from link key."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        from allauth.account.models import EmailAddress, EmailConfirmationHMAC

        key = request.data.get("key", "").strip()
        if not key:
            return Response({"detail": "Key is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Try HMAC key first (stateless, most common).  from_key() returns None
        # when the key is invalid OR when the email is already verified (it
        # queries with verified=False).  We handle the already-verified case
        # below so users get a helpful response on retry.
        confirmation = EmailConfirmationHMAC.from_key(key)

        if not confirmation:
            # Check whether the key refers to an already-verified address before
            # giving up — this happens when the view previously raised an
            # exception after saving verified=True but before returning 200.
            try:
                from django.core import signing
                from allauth.account import app_settings as allauth_settings
                max_age = int(allauth_settings.EMAIL_CONFIRMATION_EXPIRE_DAYS * 86400)
                pk = signing.loads(key, salt=allauth_settings.SALT, max_age=max_age)
                ea = EmailAddress.objects.filter(pk=pk, verified=True).first()
                if ea:
                    # Already verified — treat as success so the user can log in.
                    code = _generate_login_code(ea.user_id)
                    tenant_slug = _tenant_slug_for_user(ea.user)
                    return Response({"detail": "Email verified successfully.", "code": code, "tenant_slug": tenant_slug})
            except Exception:
                pass

            # Fallback: DB-stored confirmation (legacy / non-HMAC flow)
            try:
                from allauth.account.models import EmailConfirmation
                confirmation = EmailConfirmation.objects.get(key=key)
            except Exception:
                confirmation = None

        if not confirmation:
            return Response(
                {"detail": "Invalid or expired confirmation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify directly on the EmailAddress record to avoid allauth's
        # add_message() call which requires Django's session/messages middleware
        # and can raise MessageFailure in API contexts.
        email_address = confirmation.email_address
        if email_address.verified:
            code = _generate_login_code(email_address.user_id)
            tenant_slug = _tenant_slug_for_user(email_address.user)
            return Response({"detail": "Email verified successfully.", "code": code, "tenant_slug": tenant_slug})

        email_address.verified = True
        email_address.set_as_primary(conditional=True)
        email_address.save(update_fields=["verified", "primary"])

        # Fire the standard signal so any connected handlers run.
        from allauth.account.models import EmailAddress as EA
        from allauth.account import signals
        signals.email_confirmed.send(
            sender=EA,
            request=request,
            email_address=email_address,
        )

        logger.info("Email verified for user %s (%s)", email_address.user_id, email_address.email)
        code = _generate_login_code(email_address.user_id)
        tenant_slug = _tenant_slug_for_user(email_address.user)
        return Response({"detail": "Email verified successfully.", "code": code, "tenant_slug": tenant_slug})


class ExchangeCodeView(APIView):
    """POST /api/v1/auth/exchange-code/ — redeem a one-time login code for JWT tokens."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        code = request.data.get("code", "").strip()
        if not code:
            return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"login_code:{code}"
        user_id = cache.get(cache_key)
        if user_id is None:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete before issuing tokens — single use even if response fails
        cache.delete(cache_key)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        # Fire the login signal so handlers like the welcome notification run.
        from django.contrib.auth.signals import user_logged_in
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        user.refresh_from_db()

        access, refresh = _tokens_for_user(user)
        response = Response({
            "access": access,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        })
        _set_refresh_cookie(response, refresh)
        return response


class CheckSlugView(APIView):
    """GET /api/v1/auth/check-slug/?slug=acme — check workspace slug availability."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        from apps.authentication.serializers import RESERVED_SLUGS
        from apps.tenants.models import Tenant
        from better_profanity import profanity
        import re

        slug = request.query_params.get("slug", "").strip().lower()

        if not slug:
            return Response({"available": False, "error": "slug is required"}, status=400)

        # Validate format
        pattern = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$")
        if not pattern.match(slug):
            return Response({
                "available": False,
                "error": (
                    "Slug must be 3–50 characters: lowercase letters, numbers, and hyphens. "
                    "Cannot start or end with a hyphen."
                ),
            })

        if slug in RESERVED_SLUGS or profanity.contains_profanity(slug):
            suggestion = f"{slug}-app"
            return Response({"available": False, "suggestion": suggestion})

        if Tenant.objects.filter(slug=slug).exists():
            # Find next available suggestion
            counter = 1
            while Tenant.objects.filter(slug=f"{slug}-{counter}").exists():
                counter += 1
            return Response({"available": False, "suggestion": f"{slug}-{counter}"})

        return Response({"available": True})


class GoogleLoginView(APIView):
    """GET  /api/v1/auth/google/ — return Google OAuth authorization URL.
    POST /api/v1/auth/google/ — exchange Google OAuth code for JWT tokens.

    The client-side flow:
      1. GET  → receive {"url": "https://accounts.google.com/..."}
      2. Redirect user to that URL.
      3. Google redirects to /api/v1/auth/google/callback/ (server handles exchange).
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        from urllib.parse import urlencode
        from django.urls import reverse

        google_config = settings.SOCIALACCOUNT_PROVIDERS.get("google", {})
        client_id = google_config.get("APP", {}).get("client_id", "")
        callback_url = request.build_absolute_uri(reverse("google-callback"))

        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid profile email",
            "access_type": "online",
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return Response({"url": url})

    def post(self, request: Request) -> Response:
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
        from allauth.socialaccount.providers.oauth2.client import OAuth2Client
        from dj_rest_auth.registration.views import SocialLoginView

        # Delegate to dj-rest-auth's SocialLoginView
        view = SocialLoginView()
        view.adapter_class = GoogleOAuth2Adapter
        view.client_class = OAuth2Client
        view.request = request
        view.kwargs = {}
        view.format_kwarg = None

        try:
            inner_response = view.post(request)
        except Exception as exc:
            logger.warning("Google OAuth error: %s", exc)
            return Response(
                {"detail": "Google authentication failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return inner_response


class GoogleCallbackView(APIView):
    """GET /api/v1/auth/google/callback/ — handle OAuth redirect from Google.

    Google redirects here after the user grants permission.  This view
    exchanges the authorization code for an access token, completes the
    allauth social login (creating the user if needed), issues a JWT pair,
    and redirects the browser to the frontend callback page with the access
    token as a query parameter.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request):
        import json as json_mod
        import urllib.request
        from urllib.parse import urlencode
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from allauth.socialaccount.helpers import complete_social_login
        from allauth.socialaccount.models import SocialToken
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        code = request.query_params.get("code")
        error = request.query_params.get("error")

        if error or not code:
            return HttpResponseRedirect(f"{frontend_url}/auth/callback?error=oauth_failed")

        try:
            google_config = settings.SOCIALACCOUNT_PROVIDERS.get("google", {})
            app_config = google_config.get("APP", {})
            client_id = app_config.get("client_id", "")
            client_secret = app_config.get("secret", "")
            callback_url = request.build_absolute_uri(reverse("google-callback"))

            # Exchange authorization code for an access token directly with Google.
            token_data = urlencode({
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            }).encode()
            token_req = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=token_data,
                method="POST",
            )
            with urllib.request.urlopen(token_req) as resp:
                token_response = json_mod.loads(resp.read())

            access_token_str = token_response.get("access_token")
            if not access_token_str:
                raise ValueError("No access_token in Google token response")

            # Use allauth's adapter to fetch the Google user profile and
            # complete the social login (creates the user + social account if new).
            adapter = GoogleOAuth2Adapter(request._request)
            app = adapter.get_app(request._request)
            token_obj = SocialToken(app=app, token=access_token_str)
            social_login = adapter.complete_login(
                request._request, app, token_obj, response=token_response
            )
            social_login.token = token_obj
            complete_social_login(request._request, social_login)

            user = social_login.account.user
            if not user or not user.pk:
                raise ValueError("OAuth login did not return a valid user")

            access, refresh = _tokens_for_user(user)
            response = HttpResponseRedirect(f"{frontend_url}/auth/callback?access={access}")
            _set_refresh_cookie(response, refresh)
            return response

        except Exception as exc:
            logger.warning("Google OAuth callback error: %s", exc)
            return HttpResponseRedirect(f"{frontend_url}/auth/callback?error=oauth_failed")


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — send password-reset email."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return 200 even if email not found to prevent enumeration
            return Response({"detail": "Password reset email sent if account exists."})

        from django.contrib.sites.models import Site
        from django.template.loader import render_to_string
        from utils.email import send_email

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        combined = f"{uid}-{token}"
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_url = f"{frontend_url}/auth/reset-password?token={combined}"
        app_name = getattr(settings, "APP_NAME", "App")

        try:
            current_site = Site.objects.get_current(request)
        except Exception:
            current_site = type(
                "_Site", (), {"name": app_name, "domain": settings.BASE_DOMAIN}
            )()

        context = {
            "user": user,
            "password_reset_url": reset_url,
            "current_site": current_site,
            # key is not exposed in context — only the full URL is shown
        }

        html_body = render_to_string("account/email/password_reset_key_message.html", context)
        text_body = render_to_string("account/email/password_reset_key_message.txt", context)

        send_email(
            to=email,
            subject=f"Reset your password — {app_name}",
            html_body=html_body,
            text_body=text_body,
        )

        return Response({"detail": "Password reset email sent if account exists."})


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — set new password via token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_token: str = serializer.validated_data["token"]
        new_password: str = serializer.validated_data["new_password"]

        # Token format: "{uid64}-{token}"
        try:
            parts = raw_token.split("-", 1)
            uid = force_str(urlsafe_base64_decode(parts[0]))
            token = parts[1]
            user = User.objects.get(pk=uid)
        except Exception:
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"detail": "Password has been reset."})
