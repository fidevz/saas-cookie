"""
Custom allauth account adapter.

Overrides email confirmation URL generation to point to the Next.js frontend
instead of trying to reverse Django URL patterns (which don't exist in this
API-only backend).
"""

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class FrontendAccountAdapter(DefaultAccountAdapter):
    """Routes allauth email confirmation links to the Next.js frontend."""

    def get_email_confirmation_url(self, request, emailconfirmation) -> str:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        key = emailconfirmation.key
        return f"{frontend_url}/auth/verify-email/{key}"

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Send an HTML email so the confirmation URL is never broken by
        quoted-printable line wrapping (which splits long plain-text URLs).
        """
        from django.contrib.sites.models import Site
        from django.template.loader import render_to_string

        from utils.email import send_email

        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        app_name = getattr(settings, "APP_NAME", "App")
        to = emailconfirmation.email_address.email
        user = emailconfirmation.email_address.user

        try:
            current_site = Site.objects.get_current(request)
        except Exception:
            current_site = type(
                "_Site", (), {"name": app_name, "domain": settings.BASE_DOMAIN}
            )()

        template_prefix = (
            "account/email/email_confirmation_signup_message"
            if signup
            else "account/email/email_confirmation_message"
        )
        context = {
            "user": user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }

        html_body = render_to_string(f"{template_prefix}.html", context)
        text_body = render_to_string(f"{template_prefix}.txt", context)

        send_email(
            to=to,
            subject=f"Confirm your email — {app_name}",
            html_body=html_body,
            text_body=text_body,
        )
