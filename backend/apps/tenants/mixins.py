"""
Mixins for tenant-scoped models and views.
"""
from django.db import models


class TenantManager(models.Manager):
    """Manager that provides a ``for_tenant`` shortcut."""

    def for_tenant(self, tenant):
        """Return a queryset filtered to the given tenant."""
        return self.get_queryset().filter(tenant=tenant)


class TenantModelMixin(models.Model):
    """Abstract mixin that adds a ``tenant`` FK and a tenant-scoped manager.

    Usage::

        class MyModel(TenantModelMixin, BaseModel):
            ...
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    objects = TenantManager()

    class Meta:
        abstract = True


class TenantViewMixin:
    """DRF view mixin that scopes querysets to the current request tenant."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(self.request, "tenant", None)
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs
