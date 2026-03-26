from django.contrib import admin

from apps.teams.models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "tenant", "role", "accepted", "expires_at", "created_at"]
    list_filter = ["role", "accepted"]
    search_fields = ["email", "tenant__slug"]
    readonly_fields = ["token", "accepted_at", "created_at"]
    raw_id_fields = ["tenant", "invited_by"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("tenant", "invited_by")
