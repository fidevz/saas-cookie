from django import forms
from django.contrib import admin

from apps.subscriptions.capabilities import CAPABILITY_REGISTRY
from apps.subscriptions.models import Plan, StripeWebhookEvent, Subscription


class PlanCapabilitiesForm(forms.ModelForm):
    """
    Custom admin form for Plan that renders each capability as a dedicated
    form field (checkbox for boolean, number input for integer) rather than
    a raw JSON textarea.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = (self.instance.capabilities or {}) if self.instance.pk else {}

        for key, meta in CAPABILITY_REGISTRY.items():
            current = existing.get(key, meta["default"])
            if meta["type"] == "boolean":
                self.fields[f"cap_{key}"] = forms.BooleanField(
                    label=meta["label"],
                    required=False,
                    initial=current,
                )
            elif meta["type"] == "integer":
                unit = meta.get("unit", "")
                self.fields[f"cap_{key}"] = forms.IntegerField(
                    label=f"{meta['label']} ({unit}, blank = unlimited)",
                    required=False,
                    min_value=0,
                    initial=current,
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        capabilities = {}
        for key, meta in CAPABILITY_REGISTRY.items():
            val = self.cleaned_data.get(f"cap_{key}")
            if meta["type"] == "boolean":
                capabilities[key] = bool(val)
            elif meta["type"] == "integer":
                capabilities[key] = val  # None when left blank → unlimited
        instance.capabilities = capabilities
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Plan
        exclude = ["capabilities"]  # replaced by the individual cap_* fields above


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanCapabilitiesForm

    def get_form(self, request, obj=None, change=False, fields=None, **kwargs):
        if fields is not None:
            fields = [f for f in fields if not f.startswith("cap_")]
        return super().get_form(request, obj, change, fields=fields, **kwargs)

    list_display = ["name", "amount", "currency", "interval", "trial_days", "is_active"]
    list_filter = ["interval", "is_active", "currency"]
    search_fields = ["name", "stripe_price_id"]
    list_editable = ["is_active"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "stripe_price_id",
                    "stripe_product_id",
                    "amount",
                    "currency",
                    "interval",
                    "trial_days",
                    "is_active",
                    "features",
                ]
            },
        ),
        (
            "Capabilities",
            {
                "description": "Machine-readable feature gates. These control what the plan unlocks in the app.",
                "fields": [f"cap_{key}" for key in CAPABILITY_REGISTRY],
            },
        ),
    ]


class SubscriptionCapabilitiesForm(forms.ModelForm):
    """
    Custom admin form for Subscription that renders each capability snapshot
    as a dedicated form field instead of a raw JSON textarea.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = (self.instance.capabilities or {}) if self.instance.pk else {}

        for key, meta in CAPABILITY_REGISTRY.items():
            current = existing.get(key, meta["default"])
            if meta["type"] == "boolean":
                self.fields[f"cap_{key}"] = forms.BooleanField(
                    label=meta["label"],
                    required=False,
                    initial=current,
                )
            elif meta["type"] == "integer":
                unit = meta.get("unit", "")
                self.fields[f"cap_{key}"] = forms.IntegerField(
                    label=f"{meta['label']} ({unit}, blank = unlimited)",
                    required=False,
                    min_value=0,
                    initial=current,
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        capabilities = {}
        for key, meta in CAPABILITY_REGISTRY.items():
            val = self.cleaned_data.get(f"cap_{key}")
            if meta["type"] == "boolean":
                capabilities[key] = bool(val)
            elif meta["type"] == "integer":
                capabilities[key] = val
        instance.capabilities = capabilities
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Subscription
        exclude = ["capabilities"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    form = SubscriptionCapabilitiesForm

    def get_form(self, request, obj=None, change=False, fields=None, **kwargs):
        # cap_* fields are virtual (added in form.__init__), not model fields.
        # Strip them before modelform_factory calls fields_for_model() to avoid FieldError.
        if fields is not None:
            fields = [f for f in fields if not f.startswith("cap_")]
        return super().get_form(request, obj, change, fields=fields, **kwargs)

    list_display = [
        "tenant",
        "plan",
        "status",
        "current_period_start",
        "current_period_end",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = [
        "tenant__slug",
        "stripe_subscription_id",
        "stripe_customer_id",
    ]
    readonly_fields = [
        "stripe_subscription_id",
        "stripe_customer_id",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["tenant", "plan"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("tenant", "plan")

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "tenant",
                    "plan",
                    "status",
                    "stripe_subscription_id",
                    "stripe_customer_id",
                    "current_period_start",
                    "current_period_end",
                    "trial_end",
                    "cancelled_at",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
        (
            "Capabilities snapshot",
            {
                "description": "Snapshot of plan capabilities at subscription time. Edit these to override what this subscriber can access.",
                "fields": [f"cap_{key}" for key in CAPABILITY_REGISTRY],
            },
        ),
    ]


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "event_type", "created_at"]
    list_filter = ["event_type"]
    search_fields = ["event_id"]
    readonly_fields = ["event_id", "event_type", "created_at", "updated_at"]
    ordering = ["-created_at"]
