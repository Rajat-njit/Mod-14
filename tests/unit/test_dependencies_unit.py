# tests/unit/test_dependencies_unit.py

import uuid
import pytest
from datetime import datetime

from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User
from fastapi import HTTPException


def test_get_current_user_full_payload(monkeypatch):
    payload = {
        "id": uuid.uuid4(),
        "username": "tester",
        "email": "tester@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    monkeypatch.setattr(User, "verify_token", lambda token: payload)

    user = get_current_user(token="valid")

    assert isinstance(user, UserResponse)
    assert user.username == "tester"


def test_get_current_user_minimal_uuid(monkeypatch):
    uid = uuid.uuid4()
    monkeypatch.setattr(User, "verify_token", lambda token: uid)

    user = get_current_user(token="valid")

    assert user.id == uid
    assert user.username == "unknown"


def test_get_current_user_invalid_token(monkeypatch):
    monkeypatch.setattr(User, "verify_token", lambda token: None)

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="bad")

    assert exc.value.status_code == 401


def test_get_current_active_user_inactive():
    inactive = UserResponse(
        id=uuid.uuid4(),
        username="inactive",
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        is_active=False,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    with pytest.raises(HTTPException) as exc:
        get_current_active_user(inactive)

    assert exc.value.status_code == 400


def test_get_current_active_user_valid():
    active = UserResponse(
        id=uuid.uuid4(),
        username="active",
        email="active@example.com",
        first_name="Active",
        last_name="User",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    result = get_current_active_user(active)
    assert result.username == "active"
