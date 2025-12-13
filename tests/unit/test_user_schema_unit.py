# tests/unit/test_user_schema_unit.py

import uuid
import pytest
from datetime import datetime

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserUpdate,
    PasswordUpdate,
)


# ---------------------------
# USER CREATE
# ---------------------------

def test_user_create_valid():
    user = UserCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        username="johndoe",
        password="StrongPass123!",
        confirm_password="StrongPass123!",
    )

    assert user.username == "johndoe"


def test_user_create_password_mismatch():
    with pytest.raises(ValueError, match="Passwords do not match"):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="StrongPass123!",
            confirm_password="WrongPass123!",
        )


def test_user_create_missing_uppercase():
    with pytest.raises(ValueError, match="uppercase"):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="weakpass123!",
            confirm_password="weakpass123!",
        )


def test_user_create_missing_digit():
    with pytest.raises(ValueError, match="digit"):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="StrongPass!",
            confirm_password="StrongPass!",
        )


def test_user_create_missing_special_char():
    with pytest.raises(ValueError, match="special character"):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="StrongPass123",
            confirm_password="StrongPass123",
        )


# ---------------------------
# PASSWORD UPDATE
# ---------------------------

def test_password_update_valid():
    update = PasswordUpdate(
        current_password="OldPass123!",
        new_password="NewPass123!",
        confirm_new_password="NewPass123!",
    )

    assert update.new_password == "NewPass123!"


def test_password_update_mismatch():
    with pytest.raises(ValueError, match="do not match"):
        PasswordUpdate(
            current_password="OldPass123!",
            new_password="NewPass123!",
            confirm_new_password="WrongPass123!",
        )


def test_password_update_same_as_old():
    with pytest.raises(ValueError, match="must be different"):
        PasswordUpdate(
            current_password="SamePass123!",
            new_password="SamePass123!",
            confirm_new_password="SamePass123!",
        )


# ---------------------------
# RESPONSE / UPDATE SCHEMAS
# ---------------------------

def test_user_response_valid():
    now = datetime.utcnow()

    user = UserResponse(
        id=uuid.uuid4(),
        username="tester",
        email="tester@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )

    assert user.username == "tester"


def test_user_update_partial():
    update = UserUpdate(first_name="NewName")
    assert update.first_name == "NewName"
