"""
Core app views: feature flags + health check.
"""
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.features import FeatureFlags


class FeatureFlagsView(APIView):
    """GET /api/v1/features/ — return all feature flags."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"features": FeatureFlags.get_all_features()})


class HealthView(APIView):
    """GET /health/ — simple liveness probe."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})
