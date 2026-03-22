"""
TenantMiddleware — resolves the current tenant from the request subdomain.
"""
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

# Paths that should not trigger tenant resolution
_SKIP_PATTERNS = [
    re.compile(r"^/" + re.escape(getattr(settings, "ADMIN_URL", "tacomate")) + r"/"),
    re.compile(r"^/api/docs/"),
    re.compile(r"^/api/schema/"),
    re.compile(r"^/health/"),
]


class TenantMiddleware:
    """
    Extracts the tenant slug from the Host header and attaches the resolved
    ``Tenant`` instance to ``request.tenant``.

    For a host like ``acme.yourdomain.com`` the middleware will:
    1. Strip the BASE_DOMAIN suffix to obtain slug ``acme``.
    2. Look up ``Tenant.objects.get(slug=acme)``.
    3. Set ``request.tenant`` to the found instance, or ``None`` when the
       host is the root domain or the tenant is not found.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self._resolve_tenant(request)
        return self.get_response(request)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_tenant(self, request):
        path = request.path_info
        for pattern in _SKIP_PATTERNS:
            if pattern.match(path):
                return None

        host = request.get_host().split(":")[0].lower()  # strip port
        base_domain = getattr(settings, "BASE_DOMAIN", "localhost").lower()

        slug = self._extract_slug(host, base_domain)
        if not slug:
            return None

        return self._get_tenant(slug)

    @staticmethod
    def _extract_slug(host: str, base_domain: str) -> str | None:
        """Return the subdomain part, or None for the root domain."""
        if host == base_domain:
            return None
        if host.endswith(f".{base_domain}"):
            subdomain = host[: -(len(base_domain) + 1)]
            # Ignore 'www' and other well-known prefixes
            if subdomain in ("www", "api", ""):
                return None
            return subdomain
        # In development with localhost subdomains (e.g. acme.localhost)
        if base_domain == "localhost" and host.endswith(".localhost"):
            subdomain = host[: -len(".localhost")]
            if subdomain in ("www", "api", ""):
                return None
            return subdomain
        return None

    @staticmethod
    def _get_tenant(slug: str):
        from apps.tenants.models import Tenant

        try:
            return Tenant.objects.select_related("owner").get(slug=slug)
        except Tenant.DoesNotExist:
            logger.debug("Tenant not found for slug: %s", slug)
            return None
