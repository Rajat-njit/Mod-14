import pytest
from pydantic import ValidationError

from app.schemas.base import UserCreate, UserLogin


def test_user_create_valid_password():
    user = UserCreate(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123"
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_user_create_password_missing_uppercase():
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="securepass123"
        )


def test_user_create_password_missing_lowercase():
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="SECUREPASS123"
        )


def test_user_create_password_missing_digit():
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="SecurePass"
        )


def test_user_login_schema_valid():
    login = UserLogin(
        username="testuser",
        password="SecurePass123"
    )

    assert login.username == "testuser"
