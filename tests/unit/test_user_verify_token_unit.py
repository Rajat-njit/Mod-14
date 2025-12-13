import uuid
import pytest
from jose import JWTError, jwt

from app.models.user import User


def test_verify_token_valid(monkeypatch):
    """Valid token with UUID sub should return UUID."""
    user_id = uuid.uuid4()

    def fake_decode(token, secret, algorithms):
        return {"sub": str(user_id)}

    monkeypatch.setattr(jwt, "decode", fake_decode)

    result = User.verify_token("valid.token")

    assert isinstance(result, uuid.UUID)
    assert result == user_id


def test_verify_token_missing_sub(monkeypatch):
    """Token without sub should return None."""
    monkeypatch.setattr(jwt, "decode", lambda *a, **k: {"foo": "bar"})

    assert User.verify_token("no.sub") is None


def test_verify_token_invalid_uuid(monkeypatch):
    """Token with invalid UUID string should return None."""
    monkeypatch.setattr(jwt, "decode", lambda *a, **k: {"sub": "not-a-uuid"})

    assert User.verify_token("bad.uuid") is None



def test_verify_token_jwt_error(monkeypatch):
    """JWTError during decode should return None."""

    def raise_error(*args, **kwargs):
        raise JWTError("Invalid token")

    monkeypatch.setattr(jwt, "decode", raise_error)

    assert User.verify_token("invalid.token") is None
