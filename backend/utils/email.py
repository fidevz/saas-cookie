"""
Resend email backend for Django + convenience ``send_email`` helper.
"""

import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """
    Django email backend that delivers via the Resend API.

    Configure in settings::

        EMAIL_BACKEND = "utils.email.ResendEmailBackend"
        RESEND_API_KEY = "re_..."
        DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"
    """

    def __init__(self, fail_silently: bool = False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._api_key: str = getattr(settings, "RESEND_API_KEY", "")

    def send_messages(self, email_messages) -> int:
        """Send a list of EmailMessage objects. Returns number sent."""
        if not self._api_key:
            logger.warning(
                "RESEND_API_KEY is not set. Emails will not be sent. "
                "Set EMAIL_BACKEND to console backend for local development."
            )
            return 0

        import resend

        resend.api_key = self._api_key
        sent = 0

        for message in email_messages:
            try:
                self._send(resend, message)
                sent += 1
            except Exception as exc:
                logger.error("Failed to send email to %s: %s", message.to, exc)
                if not self.fail_silently:
                    raise

        return sent

    @staticmethod
    def _send(resend_module, message: EmailMessage) -> None:
        """Convert a Django EmailMessage to a Resend API call."""
        to = message.to if isinstance(message.to, list) else [message.to]

        # Prefer HTML content if available
        html_body = None
        text_body = message.body

        for content, mimetype in getattr(message, "alternatives", []):
            if mimetype == "text/html":
                html_body = content
                break

        params: dict = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": to,
            "subject": message.subject,
        }

        if html_body:
            params["html"] = html_body
            if text_body:
                params["text"] = text_body
        else:
            params["text"] = text_body

        if message.cc:
            params["cc"] = message.cc
        if message.bcc:
            params["bcc"] = message.bcc
        if message.reply_to:
            params["reply_to"] = [str(r) for r in message.reply_to]

        resend_module.Emails.send(params)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def send_email(
    to: str | list[str],
    subject: str,
    html_body: str,
    text_body: str = "",
    from_email: str | None = None,
) -> None:
    """
    Send an email via the configured email backend.

    Args:
        to: Recipient email(s).
        subject: Email subject line.
        html_body: HTML content.
        text_body: Plain-text fallback (optional).
        from_email: Sender address (defaults to DEFAULT_FROM_EMAIL).
    """
    from django.core.mail import EmailMultiAlternatives

    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [to] if isinstance(to, str) else to

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body or _html_to_text(html_body),
        from_email=sender,
        to=recipients,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def _html_to_text(html: str) -> str:
    """Very simple HTML → plain text stripping (no external deps)."""
    import re

    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
