"""
Authentication views: register, login, logout, token refresh, Google OAuth,
password reset.
"""
import logging

from django.conf import settings
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
from utils.throttling import LoginThrottle, RegisterThrottle

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
        user = serializer.save()

        access, refresh = _tokens_for_user(user)

        response = Response(
            {
                "access": access,
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

        # Handle first-login flag
        if user.is_first_login:
            user.is_first_login = False
            user.save(update_fields=["is_first_login"])

        access, refresh = _tokens_for_user(user)

        response = Response(
            {
                "access": access,
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


class GoogleLoginView(APIView):
    """POST /api/v1/auth/google/ — exchange Google OAuth code for JWT tokens.

    Delegates to dj-rest-auth / allauth under the hood.  The client should
    send ``{"code": "<auth_code>"}`` (server-side flow) or
    ``{"access_token": "<token>"}`` (client-side flow).
    """

    permission_classes = [AllowAny]

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

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"

        from utils.email import send_email

        send_email(
            to=email,
            subject="Password Reset Request",
            html_body=(
                f"<p>Click the link below to reset your password:</p>"
                f"<p><a href='{reset_url}'>{reset_url}</a></p>"
                f"<p>This link expires in 1 hour.</p>"
            ),
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
