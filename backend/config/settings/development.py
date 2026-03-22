"""
Development settings — never use in production.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", ".localhost"]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Use console email so we don't need Resend credentials locally
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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

# django-extensions shell_plus extras
SHELL_PLUS_PRINT_SQL = False
