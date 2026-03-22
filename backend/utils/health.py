"""
Health check URL configuration.

Included at /health/ in the root URLconf.
"""
from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok", "version": "0.1.0"})


urlpatterns = [
    path("", HealthView.as_view(), name="health"),
]
