"""
Tests for the CustomUser model.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCustomUser:
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="test@example.com", password="securepass123"
        )
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(email="", password="pass")

    def test_full_name_property(self):
        user = User(email="x@x.com", first_name="Jane", last_name="Doe")
        assert user.full_name == "Jane Doe"

    def test_full_name_falls_back_to_email(self):
        user = User(email="x@x.com")
        assert user.full_name == "x@x.com"

    def test_email_normalized(self):
        user = User.objects.create_user(email="Test@Example.COM", password="pass")
        assert user.email == "Test@example.com"

    def test_str_returns_email(self):
        user = User(email="str@example.com")
        assert str(user) == "str@example.com"
