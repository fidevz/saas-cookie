"""
Cloudflare Turnstile server-side verification.
"""

import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_token(token: str | None, remote_ip: str | None = None) -> None:
    """Verify a Turnstile challenge token.

    Raises ``PermissionError`` if the token is invalid.
    If TURNSTILE_SECRET_KEY is not configured, verification is skipped
    (allows development without a Turnstile key).
    """
    secret = getattr(settings, "TURNSTILE_SECRET_KEY", "")
    if not secret:
        logger.debug("TURNSTILE_SECRET_KEY not set — skipping Turnstile verification.")
        return

    if not token:
        raise PermissionError("Turnstile token is required.")

    payload: dict[str, str] = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(TURNSTILE_VERIFY_URL, data=data, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json

            result = json.loads(resp.read())
    except Exception as exc:
        logger.warning("Turnstile verification request failed: %s", exc)
        # Fail open on network errors — don't block legitimate users due to Cloudflare outages.
        return

    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        logger.warning("Turnstile verification failed: %s", error_codes)
        raise PermissionError("Turnstile challenge failed. Please try again.")
