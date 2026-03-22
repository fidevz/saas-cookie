"""
Notification model.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """In-app notification delivered to a user."""

    class Type(models.TextChoices):
        WELCOME = "welcome", _("Welcome")
        INFO = "info", _("Info")
        WARNING = "warning", _("Warning")
        ERROR = "error", _("Error")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user_id}"
