"""
Subscription and Plan models.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Plan(BaseModel):
    """A Stripe-backed subscription plan."""

    class Interval(models.TextChoices):
        MONTH = "month", _("Monthly")
        YEAR = "year", _("Yearly")

    name = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=255, unique=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTH)
    trial_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["amount"]
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def __str__(self):
        return f"{self.name} ({self.interval}) — {self.currency.upper()} {self.amount}"


class Subscription(BaseModel):
    """A tenant's active Stripe subscription."""

    class Status(models.TextChoices):
        TRIALING = "trialing", _("Trialing")
        ACTIVE = "active", _("Active")
        CANCELLING = "cancelling", _("Cancelling (active until period end)")
        CANCELLED = "cancelled", _("Cancelled")
        PAST_DUE = "past_due", _("Past Due")
        UNPAID = "unpaid", _("Unpaid")

    tenant = models.OneToOneField(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIALING,
    )
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.tenant.slug} — {self.status}"

    @property
    def is_active(self) -> bool:
        return self.status in (self.Status.ACTIVE, self.Status.TRIALING, self.Status.CANCELLING)
