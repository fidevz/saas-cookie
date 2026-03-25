"""
Custom allauth account adapter.

Overrides email confirmation URL generation to point to the Next.js frontend
instead of trying to reverse Django URL patterns (which don't exist in this
API-only backend).
"""
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter


class FrontendAccountAdapter(DefaultAccountAdapter):
    """Routes allauth email confirmation links to the Next.js frontend."""

    def get_email_confirmation_url(self, request, emailconfirmation) -> str:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        key = emailconfirmation.key
        return f"{frontend_url}/auth/verify-email/{key}"

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Send a plain HTML email so the confirmation URL is never broken by
        quoted-printable line wrapping (which splits long plain-text URLs).
        """
        from utils.email import send_email

        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        app_name = getattr(settings, "APP_NAME", "App")
        to = emailconfirmation.email_address.email

        html_body = (
            f"<p>Welcome to {app_name}!</p>"
            f"<p>Click the button below to verify your email address:</p>"
            f'<p><a href="{activate_url}" style="display:inline-block;padding:12px 24px;'
            f"background:#0f172a;color:#fff;text-decoration:none;border-radius:6px;"
            f'font-family:sans-serif;font-size:14px;">Verify email</a></p>'
            f"<p>Or copy and paste this link:<br>"
            f'<a href="{activate_url}">{activate_url}</a></p>'
            f"<p>This link expires in 3 days.</p>"
        )
        # text_body is intentionally empty — forces email clients and Mailhog
        # to render the HTML part where the URL is not broken by QP line wrapping
        send_email(
            to=to,
            subject=f"Confirm your email — {app_name}",
            html_body=html_body,
            text_body=" ",  # single space avoids auto-text fallback from html stripping
        )
