"""
Root URL configuration.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

admin.site.site_header = f"{settings.APP_NAME} Admin"
admin.site.site_title = f"{settings.APP_NAME} Admin"

ADMIN_URL = getattr(settings, "ADMIN_URL", "tacomate")

urlpatterns = [
    # Admin
    path(f"{ADMIN_URL}/", admin.site.urls),
    # API v1
    path(
        "api/v1/",
        include(
            [
                path("", include("apps.core.urls")),
                path("users/", include("apps.users.urls")),
                path("auth/", include("apps.authentication.urls")),
                path("tenants/", include("apps.tenants.urls")),
                path("teams/", include("apps.teams.urls")),
                path("notifications/", include("apps.notifications.urls")),
                path("subscriptions/", include("apps.subscriptions.urls")),
            ]
        ),
    ),
    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Health check
    path("health/", include("utils.health")),
]
