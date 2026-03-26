"""
Tests for the plan capability registry and validation helpers.
"""
import pytest

from apps.subscriptions.capabilities import (
    CAPABILITY_REGISTRY,
    default_capabilities,
    validate_capabilities,
)


class TestDefaultCapabilities:
    def test_returns_all_registry_keys(self):
        defaults = default_capabilities()
        assert set(defaults.keys()) == set(CAPABILITY_REGISTRY.keys())

    def test_values_match_registry_defaults(self):
        defaults = default_capabilities()
        for key, meta in CAPABILITY_REGISTRY.items():
            assert defaults[key] == meta["default"]

    def test_returns_new_dict_each_call(self):
        a = default_capabilities()
        b = default_capabilities()
        assert a == b
        assert a is not b


class TestValidateCapabilities:
    def test_valid_capabilities_returns_no_errors(self):
        caps = {"teams": True, "team_members": 5}
        assert validate_capabilities(caps) == []

    def test_valid_with_null_integer_returns_no_errors(self):
        # None means unlimited — should be accepted for integer capabilities
        caps = {"teams": False, "team_members": None}
        assert validate_capabilities(caps) == []

    def test_missing_key_returns_error(self):
        errors = validate_capabilities({"teams": True})
        assert any("Missing capability" in e for e in errors)
        assert any("team_members" in e for e in errors)

    def test_empty_dict_returns_error_for_each_key(self):
        errors = validate_capabilities({})
        assert len(errors) == len(CAPABILITY_REGISTRY)

    def test_boolean_capability_wrong_type_returns_error(self):
        caps = {"teams": "yes", "team_members": 5}
        errors = validate_capabilities(caps)
        assert len(errors) == 1
        assert "teams" in errors[0]
        assert "boolean" in errors[0]

    def test_integer_capability_wrong_type_returns_error(self):
        caps = {"teams": True, "team_members": "five"}
        errors = validate_capabilities(caps)
        assert len(errors) == 1
        assert "team_members" in errors[0]
        assert "integer" in errors[0]

    def test_multiple_errors_returned_together(self):
        caps = {"teams": "yes", "team_members": "five"}
        errors = validate_capabilities(caps)
        assert len(errors) == 2

    def test_integer_zero_is_valid(self):
        # 0 means no access — a valid value, not null
        caps = {"teams": False, "team_members": 0}
        assert validate_capabilities(caps) == []
