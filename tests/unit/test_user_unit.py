# tests/unit/test_user_unit.py

import uuid
from datetime import datetime, timezone
import pytest

from app.models.user import User
from app.auth.jwt import create_token
from app.schemas.token import TokenType


def test_hash_and_verify_password():
    password = "StrongPass123!"
    hashed = User.hash_password(password)

    assert hashed != password
    assert User.hash_password(password) != password

    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password=hashed,
    )

    assert user.verify_password(password) is True
    assert user.verify_password("WrongPassword") is False


def test_user_str_representation():
    user = User(
        id=uuid.uuid4(),
        username="jsmith",
        email="jsmith@example.com",
        first_name="John",
        last_name="Smith",
        password="hashed",
    )
    assert "John Smith" in str(user)
    assert "jsmith@example.com" in str(user)


def test_update_refreshes_updated_at():
    user = User(
        id=uuid.uuid4(),
        username="updateuser",
        email="update@example.com",
        first_name="Old",
        last_name="Name",
        password="hashed",
    )

    assert user.updated_at is None  # important expectation in unit test

    user.update(first_name="New")

    assert user.first_name == "New"
    assert user.updated_at is not None



def test_verify_token_valid():
    user_id = str(uuid.uuid4())
    token = create_token(user_id, TokenType.ACCESS)

    result = User.verify_token(token)

    assert isinstance(result, uuid.UUID)
    assert str(result) == user_id


def test_verify_token_invalid():
    assert User.verify_token("not-a-token") is None


def test_verify_token_missing_sub(monkeypatch):
    from jose import jwt

    fake_payload = {"foo": "bar"}
    monkeypatch.setattr(jwt, "decode", lambda *args, **kwargs: fake_payload)

    assert User.verify_token("fake") is None
