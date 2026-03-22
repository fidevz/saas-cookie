"""
Team management views.
"""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.features import FeatureFlags
from apps.teams.models import Invitation
from apps.teams.serializers import (
    InvitationSerializer,
    MemberSerializer,
    UpdateMemberRoleSerializer,
)
from apps.tenants.models import TenantMembership
from utils.permissions import IsTenantAdmin, IsTenantMember

logger = logging.getLogger(__name__)


def _require_tenant(request: Request):
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        raise NotFound("No tenant context for this request.")
    return tenant


def _require_feature(name: str) -> None:
    if not FeatureFlags.get_feature(name):
        raise PermissionDenied(f"Feature '{name}' is not enabled.")


class InviteMemberView(APIView):
    """POST /api/v1/teams/invitations/ — invite a new member."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_feature("TEAMS")
        tenant = _require_tenant(request)

        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Check if already a member
        if TenantMembership.objects.filter(tenant=tenant, user__email=email).exists():
            raise ValidationError({"email": "User is already a member of this tenant."})

        # Cancel any existing pending invitations for the same email
        Invitation.objects.filter(tenant=tenant, email=email, accepted=False).delete()

        invitation = serializer.save(tenant=tenant, invited_by=request.user)

        # Fire async email task
        from apps.teams.tasks import send_invitation_email

        send_invitation_email.delay(invitation.pk)

        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class AcceptInviteView(APIView):
    """POST /api/v1/teams/accept-invite/{token}/ — accept an invitation."""

    permission_classes = []  # Auth is optional — user might need to register first

    def post(self, request: Request, token: str) -> Response:
        try:
            invitation = Invitation.objects.select_related("tenant").get(token=token)
        except (Invitation.DoesNotExist, ValueError):
            raise NotFound("Invitation not found.")

        if not invitation.is_valid:
            raise ValidationError(
                "This invitation has already been accepted or has expired."
            )

        if not request.user.is_authenticated:
            return Response(
                {
                    "detail": "Authentication required to accept this invitation.",
                    "invitation": {
                        "email": invitation.email,
                        "tenant": invitation.tenant.name,
                        "role": invitation.role,
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.user.email.lower() != invitation.email.lower():
            raise PermissionDenied("This invitation was sent to a different email address.")

        # Create membership (or update role if already a member via different means)
        membership, created = TenantMembership.objects.get_or_create(
            user=request.user,
            tenant=invitation.tenant,
            defaults={"role": invitation.role},
        )
        if not created:
            membership.role = invitation.role
            membership.save(update_fields=["role"])

        invitation.accepted = True
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted", "accepted_at"])

        return Response(
            {
                "detail": "Invitation accepted.",
                "tenant": invitation.tenant.slug,
                "role": membership.role,
            }
        )


class ListMembersView(ListAPIView):
    """GET /api/v1/teams/members/ — list all members of the current tenant."""

    serializer_class = MemberSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        _require_feature("TEAMS")
        tenant = _require_tenant(self.request)
        return (
            TenantMembership.objects.filter(tenant=tenant)
            .select_related("user", "tenant")
            .order_by("created_at")
        )


class UpdateMemberRoleView(APIView):
    """PATCH /api/v1/teams/members/{id}/ — change a member's role."""

    permission_classes = [IsTenantAdmin]

    def patch(self, request: Request, pk: int) -> Response:
        _require_feature("TEAMS")
        tenant = _require_tenant(request)

        try:
            membership = TenantMembership.objects.get(pk=pk, tenant=tenant)
        except TenantMembership.DoesNotExist:
            raise NotFound("Member not found.")

        # Prevent removing the last admin
        if membership.role == TenantMembership.Role.ADMIN:
            admin_count = TenantMembership.objects.filter(
                tenant=tenant, role=TenantMembership.Role.ADMIN
            ).count()
            new_role = request.data.get("role")
            if new_role != TenantMembership.Role.ADMIN and admin_count <= 1:
                raise ValidationError("Cannot remove the last admin from the tenant.")

        serializer = UpdateMemberRoleSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(MemberSerializer(membership).data)


class RemoveMemberView(APIView):
    """DELETE /api/v1/teams/members/{id}/ — remove a member from the tenant."""

    permission_classes = [IsTenantAdmin]

    def delete(self, request: Request, pk: int) -> Response:
        _require_feature("TEAMS")
        tenant = _require_tenant(request)

        try:
            membership = TenantMembership.objects.get(pk=pk, tenant=tenant)
        except TenantMembership.DoesNotExist:
            raise NotFound("Member not found.")

        if membership.user == request.user:
            raise ValidationError("You cannot remove yourself from the tenant.")

        # Prevent removing the last admin
        if membership.role == TenantMembership.Role.ADMIN:
            admin_count = TenantMembership.objects.filter(
                tenant=tenant, role=TenantMembership.Role.ADMIN
            ).count()
            if admin_count <= 1:
                raise ValidationError("Cannot remove the last admin from the tenant.")

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
