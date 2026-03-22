from django.contrib import admin

from apps.subscriptions.models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "amount", "currency", "interval", "trial_days", "is_active"]
    list_filter = ["interval", "is_active", "currency"]
    search_fields = ["name", "stripe_price_id"]
    list_editable = ["is_active"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
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
