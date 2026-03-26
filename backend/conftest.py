"""
pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_feature_flags(settings):
    """Ensure feature flags are reset to enabled by default in tests."""
    settings.FEATURE_FLAGS = {
        "TEAMS": True,
        "BILLING": True,
        "NOTIFICATIONS": True,
    }


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """
    Clear Django's cache before each test so rate-limiter state doesn't
    carry over between tests when they all share the same test IP address.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def close_db_connections_after_test():
    """
    Close all DB connections after every test.
    Critical for async (Channels/WebSocket) tests where connections opened
    in worker threads can block test DB teardown.
    """
    yield
    from django.db import connections

    connections.close_all()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        email="fixture@example.com",
        password="testpassword123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def auth_api_client(user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client
