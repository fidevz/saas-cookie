from django.urls import path

from apps.authentication.views import (
    CheckSlugView,
    GoogleCallbackView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ResendVerificationView,
    TokenRefreshCookieView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshCookieView.as_view(), name="token-refresh"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("check-slug/", CheckSlugView.as_view(), name="check-slug"),
]
