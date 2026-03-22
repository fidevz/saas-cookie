"""
pytest configuration and shared fixtures.
"""
import django
import pytest
from django.conf import settings


@pytest.fixture(autouse=True)
def reset_feature_flags(settings):
    """Ensure feature flags are reset to enabled by default in tests."""
    settings.FEATURE_FLAGS = {
        "TEAMS": True,
        "BILLING": True,
        "NOTIFICATIONS": True,
    }


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
