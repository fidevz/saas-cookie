"""
Development settings — never use in production.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", ".localhost"]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Email via Mailhog (SMTP local) — UI at http://localhost:8025
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False

# Use in-memory channel layer so Redis isn't required in dev
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# JWT cookies don't need Secure flag over HTTP in dev
SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    "AUTH_COOKIE_SECURE": False,
}

REST_AUTH = {
    **REST_AUTH,  # noqa: F405
    "JWT_AUTH_SECURE": False,
}

# Local database override (can also be set via DATABASE_URL in .env)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "saas_boilerplate",
        "USER": "",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Relax throttling in development (high limits for testing)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/hour",
        "user": "100000/hour",
        "login": "1000/minute",
        "register": "1000/minute",
        "resend_verification": "1000/hour",
    },
}

# Run Celery tasks synchronously in development (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# django-extensions shell_plus extras
SHELL_PLUS_PRINT_SQL = False
