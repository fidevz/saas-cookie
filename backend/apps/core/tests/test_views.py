"""
Tests for core app views: FeatureFlagsView and SupportView.
"""
import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestFeatureFlagsView:
    url = "/api/v1/features/"

    def test_returns_all_flags(self, client):
        flags = {"TEAMS": True, "BILLING": False, "NOTIFICATIONS": True}
        with override_settings(FEATURE_FLAGS=flags):
            response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["features"] == flags

    def test_accessible_without_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_returns_empty_when_no_flags_configured(self, client):
        with override_settings(FEATURE_FLAGS={}):
            response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["features"] == {}


@pytest.mark.django_db
class TestSupportView:
    url = "/api/v1/support/"

    valid_payload = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "subject": "Need help",
        "message": "I have a question about billing.",
    }

    def test_accepts_valid_submission(self, client):
        response = client.post(self.url, self.valid_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data

    def test_accessible_without_auth(self, client):
        response = client.post(self.url, self.valid_payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_rejects_missing_name(self, client):
        payload = {**self.valid_payload, "name": ""}
        response = client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_rejects_invalid_email(self, client):
        payload = {**self.valid_payload, "email": "not-an-email"}
        response = client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_rejects_missing_message(self, client):
        payload = {**self.valid_payload, "message": ""}
        response = client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_missing_subject(self, client):
        payload = {**self.valid_payload, "subject": ""}
        response = client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
