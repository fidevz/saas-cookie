"""
Celery tasks for team invitations.
"""

import logging
from urllib.parse import urlparse

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string


def _tenant_invite_url(tenant_slug: str, token: str) -> str:
    """Return the invite accept URL on the tenant's subdomain."""
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    base_domain = getattr(settings, "BASE_DOMAIN", "localhost")
    parsed = urlparse(frontend_url)
    host = f"{tenant_slug}.{base_domain}"
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return f"{parsed.scheme}://{host}/invite/{token}"


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invitation_email(self, invitation_id: int) -> None:
    """Send a team invitation email via Resend."""
    from apps.teams.models import Invitation
    from utils.email import send_email

    try:
        invitation = Invitation.objects.select_related("tenant", "invited_by").get(
            pk=invitation_id
        )
    except Invitation.DoesNotExist:
        logger.error("Invitation %s not found", invitation_id)
        return

    app_name = settings.APP_NAME
    accept_url = _tenant_invite_url(invitation.tenant.slug, invitation.token)
    invited_by_name = (
        invitation.invited_by.full_name if invitation.invited_by else app_name
    )

    context = {
        "app_name": app_name,
        "inviter_name": invited_by_name,
        "team_name": invitation.tenant.name,
        "invitation_url": accept_url,
        "role": invitation.role,
    }

    subject = f"You've been invited to join {invitation.tenant.name} on {app_name}"
    html_body = render_to_string("teams/email/invitation.html", context)
    text_body = render_to_string("teams/email/invitation.txt", context)

    try:
        send_email(
            to=invitation.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        logger.info(
            "Invitation email sent to %s (invitation %s)",
            invitation.email,
            invitation_id,
        )
    except Exception as exc:
        logger.warning("Failed to send invitation email: %s", exc)
        raise self.retry(exc=exc)
