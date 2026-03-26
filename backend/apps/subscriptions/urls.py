from django.urls import path

from apps.subscriptions.views import (
    CancelSubscriptionView,
    CreateCheckoutSessionView,
    CurrentSubscriptionView,
    CustomerPortalView,
    ListPlansView,
    SelectFreePlanView,
    WebhookView,
)

urlpatterns = [
    path("plans/", ListPlansView.as_view(), name="plan-list"),
    path("current/", CurrentSubscriptionView.as_view(), name="subscription-current"),
    path(
        "checkout/", CreateCheckoutSessionView.as_view(), name="subscription-checkout"
    ),
    path("portal/", CustomerPortalView.as_view(), name="subscription-portal"),
    path("cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("select-free/", SelectFreePlanView.as_view(), name="subscription-select-free"),
    path("webhook/", WebhookView.as_view(), name="stripe-webhook"),
]
