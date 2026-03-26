"""
Tenant and membership models for multi-tenant support.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Tenant(BaseModel):
    """An organisation / workspace identified by a unique slug (subdomain)."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=63, unique=True, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_tenants",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return f"{self.name} ({self.slug})"


class TenantMembership(BaseModel):
    """Links a user to a tenant with a specific role."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    class Meta:
        unique_together = [("user", "tenant")]
        verbose_name = "Tenant Membership"
        verbose_name_plural = "Tenant Memberships"

    def __str__(self):
        return f"{self.user.email} → {self.tenant.slug} ({self.role})"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN
