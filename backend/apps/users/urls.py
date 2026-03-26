from django.urls import path

from apps.users.views import (
    EmailChangeCancelView,
    EmailChangeConfirmView,
    EmailChangeRequestView,
    ProfileView,
)

urlpatterns = [
    path("me/", ProfileView.as_view(), name="user-profile"),
    path("me/email/", EmailChangeRequestView.as_view(), name="email-change-request"),
    path("me/email/confirm/", EmailChangeConfirmView.as_view(), name="email-change-confirm"),
    path("me/email/cancel/", EmailChangeCancelView.as_view(), name="email-change-cancel"),
]
