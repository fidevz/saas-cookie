"""
Feature flag helpers — reads FEATURE_FLAGS dict from Django settings.
"""
from django.conf import settings


class FeatureFlags:
    """Centralised access to feature flags defined in settings.FEATURE_FLAGS."""

    @staticmethod
    def get_feature(name: str) -> bool:
        """Return the boolean value for a feature flag.

        Args:
            name: Flag name without the ``FEATURE_`` prefix, e.g. ``"TEAMS"``.

        Returns:
            ``True`` if the feature is enabled, ``False`` otherwise.
        """
        flags: dict = getattr(settings, "FEATURE_FLAGS", {})
        return bool(flags.get(name.upper(), False))

    @staticmethod
    def get_all_features() -> dict:
        """Return a dict of all feature flags and their current values."""
        return dict(getattr(settings, "FEATURE_FLAGS", {}))

    # Convenience shortcuts
    @classmethod
    def teams_enabled(cls) -> bool:
        return cls.get_feature("TEAMS")

    @classmethod
    def billing_enabled(cls) -> bool:
        return cls.get_feature("BILLING")

    @classmethod
    def notifications_enabled(cls) -> bool:
        return cls.get_feature("NOTIFICATIONS")

    @classmethod
    def require_subscription(cls) -> bool:
        return cls.get_feature("REQUIRE_SUBSCRIPTION")
