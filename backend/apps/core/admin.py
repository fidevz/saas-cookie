from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "tenant", "actor", "action", "target"]
    list_filter = ["action"]
    search_fields = ["actor__email", "action", "target", "tenant__slug"]
    fields = ["actor_link", "tenant_link", "action", "target", "metadata", "timestamp"]
    readonly_fields = ["actor_link", "tenant_link", "action", "target", "metadata", "timestamp"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("actor", "tenant")

    @admin.display(description="Actor")
    def actor_link(self, obj):
        if not obj.actor:
            return "—"
        url = reverse("admin:users_customuser_change", args=[obj.actor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.actor.email)

    @admin.display(description="Tenant")
    def tenant_link(self, obj):
        if not obj.tenant:
            return "—"
        url = reverse("admin:tenants_tenant_change", args=[obj.tenant.pk])
        return format_html('<a href="{}">{}</a>', url, obj.tenant.slug)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
