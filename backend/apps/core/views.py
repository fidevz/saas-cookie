"""
Core app views: feature flags + support contact.
"""

import html as html_lib
import logging

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.features import FeatureFlags
from apps.core.serializers import SupportSerializer
from utils.email import send_email

logger = logging.getLogger(__name__)


class FeatureFlagsView(APIView):
    """GET /api/v1/features/ — return all feature flags."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"features": FeatureFlags.get_all_features()})


class SupportView(APIView):
    """POST /api/v1/support/ — submit a support contact form."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SupportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        support_email = getattr(settings, "SUPPORT_EMAIL", "support@example.com")

        try:
            send_email(
                to=[support_email],
                subject=f"[Support] {html_lib.escape(data['subject'])}",
                html_body=(
                    f"<p><strong>From:</strong> {html_lib.escape(data['name'])} &lt;{html_lib.escape(data['email'])}&gt;</p>"
                    f"<p><strong>Subject:</strong> {html_lib.escape(data['subject'])}</p>"
                    f"<hr><p>{html_lib.escape(data['message'])}</p>"
                ),
            )
        except Exception:
            logger.exception("Failed to send support email from %s", data.get("email"))
            # Still return success — do not expose email delivery failures to users

        return Response({"detail": "Message received."})
