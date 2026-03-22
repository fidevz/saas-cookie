"""
User profile views.
"""
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.users.models import CustomUser
from apps.users.serializers import UserProfileSerializer


class ProfileView(RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/users/me/ — retrieve or update the authenticated user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self) -> CustomUser:
        return self.request.user
