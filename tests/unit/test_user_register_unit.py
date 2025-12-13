# tests/unit/test_user_register_unit.py

import uuid
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
    def __init__(self, existing_user=None):
        self._existing_user = existing_user
        self.added = None

    def query(self, model):
        return DummyQuery(self._existing_user)

    def add(self, obj):
        self.added = obj


def test_register_password_too_short():
    db = DummyDB()

    user_data = {
        "username": "shortpass",
        "email": "short@example.com",
        "first_name": "Short",
        "last_name": "Pass",
        "password": "123",
    }

    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        User.register(db, user_data)


def test_register_duplicate_user():
    existing = User(
        id=uuid.uuid4(),
        username="existing",
        email="existing@example.com",
        first_name="Ex",
        last_name="User",
        password="hashed",
    )

    db = DummyDB(existing_user=existing)

    user_data = {
        "username": "existing",
        "email": "existing@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPass123",
    }

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db, user_data)


def test_register_success():
    db = DummyDB(existing_user=None)

    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPass123",
    }

    user = User.register(db, user_data)

    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.password != "StrongPass123"  # hashed
    assert db.added is user
