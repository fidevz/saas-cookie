from django.urls import path

from apps.notifications.views import (
    ClearReadNotificationsView,
    DeleteNotificationView,
    ListNotificationsView,
    MarkAllReadView,
    MarkReadView,
)

urlpatterns = [
    path("", ListNotificationsView.as_view(), name="notification-list"),
    path("read-all/", MarkAllReadView.as_view(), name="notification-read-all"),
    path("clear-read/", ClearReadNotificationsView.as_view(), name="notification-clear-read"),
    path("<int:pk>/read/", MarkReadView.as_view(), name="notification-read"),
    path("<int:pk>/", DeleteNotificationView.as_view(), name="notification-delete"),
]
