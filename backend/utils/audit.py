"""
Audit logging helpers.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def log_action(
    actor,
    action: str,
    target: str = "",
    metadata: dict | None = None,
    tenant=None,
) -> None:
    """
    Create an immutable AuditLog entry.

    Args:
        actor: The user (or None for anonymous/system actions).
        action: Short action description, e.g. ``"user.login"``.
        target: Optional identifier for the affected object.
        metadata: Optional dict with additional context.
        tenant: The tenant this action belongs to (or None for system actions).
    """
    from apps.core.models import AuditLog

    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            target=target,
            metadata=metadata or {},
            tenant=tenant,
        )
    except Exception as exc:
        # Audit logging should never break the main flow
        logger.error("Failed to create audit log [%s]: %s", action, exc)
