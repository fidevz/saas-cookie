from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "title", "read", "created_at"]
    list_filter = ["type", "read"]
    search_fields = ["user__email", "title", "body"]
    readonly_fields = ["user", "type", "title", "body", "created_at"]
    raw_id_fields = ["user"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
