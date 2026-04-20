"""
Core middleware.
"""


class HealthCheckMiddleware:
    """Bypass ALLOWED_HOSTS for health-check requests from reverse proxies.

    Coolify/Kamal proxy sends health checks with Host: localhost (or hits the
    container IP directly). Django's SecurityMiddleware rejects those unless
    the host is in ALLOWED_HOSTS. This middleware patches the Host header
    before SecurityMiddleware runs so /health/ is always reachable.

    Must be the *first* entry in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info == "/health/":
            from django.conf import settings

            # Pick the first concrete host (skip wildcards and .localhost).
            allowed = [
                h for h in settings.ALLOWED_HOSTS if h not in ("*", ".localhost")
            ]
            request.META["HTTP_HOST"] = allowed[0] if allowed else "localhost"
        return self.get_response(request)
