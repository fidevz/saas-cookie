from django.urls import path

from apps.core.views import FeatureFlagsView, SupportView

urlpatterns = [
    path("features/", FeatureFlagsView.as_view(), name="feature-flags"),
    path("support/", SupportView.as_view(), name="support-contact"),
]
