from django.urls import path

from apps.teams.views import (
    AcceptInviteView,
    InviteMemberView,
    ListMembersView,
    RemoveMemberView,
    UpdateMemberRoleView,
)

urlpatterns = [
    path("invitations/", InviteMemberView.as_view(), name="team-invite"),
    path("members/", ListMembersView.as_view(), name="team-members"),
    path("members/<int:pk>/", UpdateMemberRoleView.as_view(), name="team-member-role"),
    path("members/<int:pk>/remove/", RemoveMemberView.as_view(), name="team-member-remove"),
    path("accept-invite/<uuid:token>/", AcceptInviteView.as_view(), name="accept-invite"),
]
