"""
Custom user model — email-based, no mandatory username.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.managers import CustomUserManager


class CustomUser(AbstractUser):
    """Extended user model with email as the primary identifier."""

    # Remove username requirement; make email unique
    username = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(unique=True)

    # Pending email change — set when a change is requested, cleared on confirm/cancel
    pending_email = models.EmailField(blank=True, default="")

    # User's preferred UI theme (applied in protected views only)
    THEME_CHOICES = [("system", "System"), ("light", "Light"), ("dark", "Dark")]
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default="light",
    )

    # Track first-time logins for welcome notification
    is_first_login = models.BooleanField(
        default=True,
        help_text="Set to False after the first successful login.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email
