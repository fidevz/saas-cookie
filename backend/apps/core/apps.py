from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "Core"

    def ready(self):
        """Validate required environment variables on startup (production only)."""
        self._validate_required_env_vars()

    def _validate_required_env_vars(self):
        # Import lazily to avoid circular import issues during app loading.
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured

        # Only enforce in production (DEBUG=False). Development allows empty
        # values so engineers can run the project with minimal configuration.
        if settings.DEBUG:
            return

        required = {
            "SECRET_KEY": getattr(settings, "SECRET_KEY", ""),
            "DATABASE_URL": getattr(settings, "DATABASE_URL", ""),
            "RESEND_API_KEY": getattr(settings, "RESEND_API_KEY", ""),
            "STRIPE_SECRET_KEY": getattr(settings, "STRIPE_SECRET_KEY", ""),
            "STRIPE_WEBHOOK_SECRET": getattr(settings, "STRIPE_WEBHOOK_SECRET", ""),
        }

        missing = [name for name, value in required.items() if not value]

        if missing:
            raise ImproperlyConfigured(
                "The following required environment variables are not set: "
                + ", ".join(missing)
                + ". Set them before starting the server in production."
            )
