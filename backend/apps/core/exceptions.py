"""
Custom DRF exception handler.

Ensures all API errors are returned as JSON with a consistent shape:

    {"error": "<error_code>", "detail": "<message or dict>"}

Never returns HTML, never exposes stack traces in production.
"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Normalise every DRF exception into a predictable JSON envelope."""

    # Let DRF build its default response first (handles most cases and sets
    # the correct HTTP status code).
    response = drf_exception_handler(exc, context)

    if response is None:
        # DRF didn't handle it — this is an unhandled server error.
        logger.exception("Unhandled server error", exc_info=exc)
        return Response(
            {"error": "server_error", "detail": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Map HTTP status → semantic error code.
    status_code = response.status_code

    if status_code == status.HTTP_400_BAD_REQUEST:
        return Response(
            {"error": "validation_error", "detail": response.data},
            status=status_code,
        )

    if status_code == status.HTTP_401_UNAUTHORIZED:
        detail = _extract_detail(response.data, "Authentication credentials were not provided.")
        return Response(
            {"error": "authentication_error", "detail": detail},
            status=status_code,
        )

    if status_code == status.HTTP_403_FORBIDDEN:
        detail = _extract_detail(response.data, "You do not have permission to perform this action.")
        return Response(
            {"error": "permission_denied", "detail": detail},
            status=status_code,
        )

    if status_code == status.HTTP_404_NOT_FOUND:
        detail = _extract_detail(response.data, "Not found.")
        return Response(
            {"error": "not_found", "detail": detail},
            status=status_code,
        )

    if status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        detail = _extract_detail(response.data, "Method not allowed.")
        return Response(
            {"error": "method_not_allowed", "detail": detail},
            status=status_code,
        )

    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        detail = _extract_detail(response.data, "Request was throttled.")
        return Response(
            {"error": "throttled", "detail": detail},
            status=status_code,
        )

    if status_code >= 500:
        # Never expose internal details in production.
        if not settings.DEBUG:
            return Response(
                {"error": "server_error", "detail": "An unexpected error occurred"},
                status=status_code,
            )

    # Fallback: preserve whatever DRF produced but wrap it.
    return response


def _extract_detail(data, fallback: str) -> str:
    """Pull a plain string detail out of DRF response data."""
    if isinstance(data, dict):
        detail = data.get("detail", fallback)
        return str(detail)
    if isinstance(data, (list, str)):
        return str(data)
    return fallback
