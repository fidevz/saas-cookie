from django.urls import path

from apps.tenants.views import TenantDetailView, TenantMembershipListView

urlpatterns = [
    path("current/", TenantDetailView.as_view(), name="tenant-detail"),
    path("members/", TenantMembershipListView.as_view(), name="tenant-members"),
]
