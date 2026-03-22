from django.urls import path

from apps.core.views import FeatureFlagsView

urlpatterns = [
    path("features/", FeatureFlagsView.as_view(), name="feature-flags"),
]
