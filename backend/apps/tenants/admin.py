from django.contrib import admin

from apps.tenants.models import Tenant, TenantMembership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "created_at"]
    search_fields = ["name", "slug", "owner__email"]
    list_filter = ["created_at"]
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ["owner"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner")


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "role", "created_at"]
    list_filter = ["role"]
    search_fields = ["user__email", "tenant__slug"]
    raw_id_fields = ["user", "tenant"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "tenant")
