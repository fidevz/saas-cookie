"""
Celery application configuration.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("config")

# Read config from Django settings with CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic task schedule (requires celery beat to be running)
app.conf.beat_schedule = {
    "check-trial-endings-daily": {
        "task": "apps.subscriptions.tasks.check_trial_endings",
        "schedule": crontab(hour=9, minute=0),  # Every day at 09:00 UTC
    },
    "cleanup-unverified-tenants": {
        "task": "apps.tenants.tasks.cleanup_unverified_tenants",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
