"""
Celery tasks for team invitations.
"""
import logging

from celery import shared_task
from django.conf import settings

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
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    accept_url = f"{frontend_url}/invite/{invitation.token}"
    invited_by_name = (
        invitation.invited_by.full_name if invitation.invited_by else app_name
    )

    subject = f"You've been invited to join {invitation.tenant.name} on {app_name}"
    html_body = f"""
    <h2>You've been invited!</h2>
    <p>{invited_by_name} has invited you to join <strong>{invitation.tenant.name}</strong>
    on {app_name} as a <strong>{invitation.role}</strong>.</p>
    <p>
        <a href="{accept_url}" style="
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
        ">Accept Invitation</a>
    </p>
    <p>This invitation expires in 48 hours.</p>
    <p>If you did not expect this email, you can ignore it.</p>
    """

    try:
        send_email(to=invitation.email, subject=subject, html_body=html_body)
        logger.info("Invitation email sent to %s (invitation %s)", invitation.email, invitation_id)
    except Exception as exc:
        logger.warning("Failed to send invitation email: %s", exc)
        raise self.retry(exc=exc)
