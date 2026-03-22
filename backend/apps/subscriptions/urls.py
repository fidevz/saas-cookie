from django.urls import path

from apps.subscriptions.views import (
    CancelSubscriptionView,
    CreateCheckoutSessionView,
    CustomerPortalView,
    ListPlansView,
    WebhookView,
)

urlpatterns = [
    path("plans/", ListPlansView.as_view(), name="plan-list"),
    path("checkout/", CreateCheckoutSessionView.as_view(), name="subscription-checkout"),
    path("portal/", CustomerPortalView.as_view(), name="subscription-portal"),
    path("cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("webhook/", WebhookView.as_view(), name="stripe-webhook"),
]
