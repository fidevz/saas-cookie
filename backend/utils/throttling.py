"""
Custom DRF throttle classes for auth endpoints.
"""
from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    """5 login attempts per minute per IP."""

    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    """3 registration attempts per minute per IP."""

    scope = "register"
