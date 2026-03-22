"""
Team invitation model.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.tenants.models import TenantMembership


class Invitation(models.Model):
    """Pending invitation to join a tenant workspace."""

    email = models.EmailField()
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    role = models.CharField(
        max_length=20,
        choices=TenantMembership.Role.choices,
        default=TenantMembership.Role.MEMBER,
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    expires_at = models.DateTimeField()
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite {self.email} → {self.tenant.slug} ({self.role})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.accepted and not self.is_expired
