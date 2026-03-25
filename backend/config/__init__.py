# This ensures the Celery app is always imported when Django starts
# so shared_task will use the properly configured app.
from .celery import app as celery_app

__all__ = ("celery_app",)
