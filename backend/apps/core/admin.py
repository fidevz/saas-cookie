from django.contrib import admin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor", "action", "target"]
    list_filter = ["action"]
    search_fields = ["actor__email", "action", "target"]
    readonly_fields = ["actor", "action", "target", "metadata", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
