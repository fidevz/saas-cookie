"""
Tests for FeatureFlags.
"""

from django.test import override_settings

from apps.core.features import FeatureFlags


class TestFeatureFlags:
    def test_get_feature_returns_true_when_enabled(self):
        with override_settings(FEATURE_FLAGS={"TEAMS": True}):
            assert FeatureFlags.get_feature("TEAMS") is True

    def test_get_feature_returns_false_when_disabled(self):
        with override_settings(FEATURE_FLAGS={"TEAMS": False}):
            assert FeatureFlags.get_feature("TEAMS") is False

    def test_get_feature_returns_false_for_unknown_flag(self):
        with override_settings(FEATURE_FLAGS={}):
            assert FeatureFlags.get_feature("NONEXISTENT") is False

    def test_teams_enabled_shortcut(self):
        with override_settings(FEATURE_FLAGS={"TEAMS": True}):
            assert FeatureFlags.teams_enabled() is True
        with override_settings(FEATURE_FLAGS={"TEAMS": False}):
            assert FeatureFlags.teams_enabled() is False

    def test_billing_enabled_shortcut(self):
        with override_settings(FEATURE_FLAGS={"BILLING": True}):
            assert FeatureFlags.billing_enabled() is True

    def test_notifications_enabled_shortcut(self):
        with override_settings(FEATURE_FLAGS={"NOTIFICATIONS": True}):
            assert FeatureFlags.notifications_enabled() is True

