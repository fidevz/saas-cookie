"""
Subscription serializers.
"""
from rest_framework import serializers

from apps.subscriptions.models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    def get_amount(self, obj):
        return int(obj.amount * 100)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "stripe_price_id",
            "amount",
            "currency",
            "interval",
            "trial_days",
            "features",
            "capabilities",
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "tenant_slug",
            "plan",
            "status",
            "capabilities",
            "current_period_start",
            "current_period_end",
            "trial_end",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
