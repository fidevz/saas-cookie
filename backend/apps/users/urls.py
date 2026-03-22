from django.urls import path

from apps.users.views import ProfileView

urlpatterns = [
    path("me/", ProfileView.as_view(), name="user-profile"),
]
