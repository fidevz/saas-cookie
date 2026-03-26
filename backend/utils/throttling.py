"""
Custom DRF throttle classes for auth endpoints.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginThrottle(AnonRateThrottle):
    """5 login attempts per minute per IP."""

    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    """3 registration attempts per minute per IP."""

    scope = "register"


class ResendVerificationThrottle(AnonRateThrottle):
    """1 resend request per 5 minutes per IP."""

    scope = "resend_verification"


class EmailChangeThrottle(UserRateThrottle):
    """3 email change requests per hour per user."""

    scope = "email_change"
