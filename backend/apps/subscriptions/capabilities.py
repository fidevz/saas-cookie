"""
Plan capability registry.

Capabilities are machine-readable feature gates tied to a subscription plan.
They are distinct from Plan.features, which contains marketing display copy.

Types:
  - "boolean": Feature is on or off. Value must be True or False.
  - "integer": Numeric limit. None means unlimited; 0 means no access.

Every plan must define every capability key.  Plan.clean() enforces this at
save time, and the Django admin renders proper form inputs for each type.
"""

CAPABILITY_REGISTRY: dict[str, dict] = {
    "teams": {
        "type": "boolean",
        "label": "Team Management",
        "default": False,
    },
    "team_members": {
        "type": "integer",
        "label": "Max team members",
        "default": 1,
        "unit": "members",
    },
}


def default_capabilities() -> dict:
    """Return a capabilities dict populated with registry defaults."""
    return {key: meta["default"] for key, meta in CAPABILITY_REGISTRY.items()}


def validate_capabilities(capabilities: dict) -> list[str]:
    """
    Validate a capabilities dict against the registry.
    Returns a list of error strings; empty list means valid.
    """
    errors: list[str] = []
    for key, meta in CAPABILITY_REGISTRY.items():
        if key not in capabilities:
            errors.append(f"Missing capability: '{key}'.")
            continue
        value = capabilities[key]
        expected_type = meta["type"]
        if expected_type == "boolean" and not isinstance(value, bool):
            errors.append(
                f"Capability '{key}' must be a boolean, got {type(value).__name__}."
            )
        elif (
            expected_type == "integer"
            and value is not None
            and not isinstance(value, int)
        ):
            errors.append(
                f"Capability '{key}' must be an integer or null, got {type(value).__name__}."
            )
    return errors
