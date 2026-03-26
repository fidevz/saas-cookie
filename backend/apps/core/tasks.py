"""
Celery tasks for core app.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_audit_logs(days: int = 90) -> None:
    """Delete AuditLog entries older than `days` to prevent table bloat."""
    from apps.core.models import AuditLog

    cutoff = timezone.now() - timedelta(days=days)
    count, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
    logger.info("Deleted %d audit logs older than %d days", count, days)
