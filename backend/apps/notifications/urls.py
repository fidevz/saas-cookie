from django.urls import path

from apps.notifications.views import (
    ListNotificationsView,
    MarkAllReadView,
    MarkReadView,
)

urlpatterns = [
    path("", ListNotificationsView.as_view(), name="notification-list"),
    path("read-all/", MarkAllReadView.as_view(), name="notification-read-all"),
    path("<int:pk>/read/", MarkReadView.as_view(), name="notification-read"),
]
