# tests/unit/test_user_authenticate_unit.py

import uuid
from datetime import timezone
import pytest

from app.models.user import User


class DummyQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class DummyDB:
    def __init__(self, user=None):
        self.user = user
        self.flushed = False

    def query(self, model):
        return DummyQuery(self.user)

    def flush(self):
        self.flushed = True


def test_authenticate_user_not_found():
    db = DummyDB(user=None)

    result = User.authenticate(db, "missing", "password")

    assert result is None


def test_authenticate_wrong_password(monkeypatch):
    user = User(
        id=uuid.uuid4(),
        username="user",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password="hashed",
    )

    monkeypatch.setattr(user, "verify_password", lambda pw: False)

    db = DummyDB(user=user)

    result = User.authenticate(db, "user", "wrong")

    assert result is None


def test_authenticate_success(monkeypatch):
    user = User(
        id=uuid.uuid4(),
        username="user",
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password="hashed",
    )

    monkeypatch.setattr(user, "verify_password", lambda pw: True)
    monkeypatch.setattr(User, "create_access_token", lambda data: "access-token")
    monkeypatch.setattr(User, "create_refresh_token", lambda data: "refresh-token")

    db = DummyDB(user=user)

    result = User.authenticate(db, "user", "correct")

    assert result["access_token"] == "access-token"
    assert result["refresh_token"] == "refresh-token"
    assert result["token_type"] == "bearer"
    assert result["user"] is user
    assert user.last_login is not None
    assert db.flushed is True
