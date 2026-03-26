from django.contrib import admin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "tenant", "actor", "action", "target"]
    list_filter = ["action", "tenant__slug"]
    search_fields = ["actor__email", "action", "target", "tenant__slug"]
    readonly_fields = ["actor", "tenant", "action", "target", "metadata", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
