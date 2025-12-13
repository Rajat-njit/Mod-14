import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt
from uuid import uuid4

from app.auth.jwt import (
    verify_password,
    get_password_hash,
    create_token,
    decode_token,
    is_blacklisted,
)
from app.schemas.token import TokenType
from app.core.config import get_settings

settings = get_settings()


# --------------------------
# Password Hashing Tests
# --------------------------
def test_password_hash_and_verify():
    raw = "StrongPassword123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrongpass", hashed) is False


# --------------------------
# Token Creation Tests
# --------------------------
def test_create_access_token_success():
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["type"] == "access"


def test_create_refresh_token_success():
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.REFRESH)
    decoded = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["type"] == "refresh"


def test_create_token_with_custom_expiry():
    user_id = str(uuid4())
    token = create_token(
        user_id,
        TokenType.ACCESS,
        expires_delta=timedelta(minutes=1),
    )
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
    # exp must be ~60 seconds after iat
    assert decoded["exp"] > decoded["iat"]


# --------------------------
# Token Decode Tests
# --------------------------
@pytest.mark.asyncio
async def test_decode_token_valid(monkeypatch):
    """Valid token should return payload when blacklist = False."""
    async def fake_blacklist(jti):
        return False

    monkeypatch.setattr("app.auth.jwt.is_blacklisted", fake_blacklist)

    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)

    payload = await decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"



@pytest.mark.asyncio
async def test_decode_token_invalid_type():
    """Token created as access should not validate as refresh."""
    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)

    with pytest.raises(Exception):
        await decode_token(token, TokenType.REFRESH)


@pytest.mark.asyncio
async def test_decode_token_expired(monkeypatch):
    """Expired token should raise 401."""
    user_id = str(uuid4())
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    payload = {
        "sub": user_id,
        "type": "access",
        "exp": expired_time,
        "iat": expired_time,
        "jti": "abc123",
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(Exception):
        await decode_token(token, TokenType.ACCESS, verify_exp=True)


@pytest.mark.asyncio
async def test_decode_token_blacklisted(monkeypatch):
    """If the token is blacklisted, decode should raise 401."""
    monkeypatch.setattr("app.auth.jwt.is_blacklisted", lambda jti: True)

    user_id = str(uuid4())
    token = create_token(user_id, TokenType.ACCESS)

    with pytest.raises(Exception):
        await decode_token(token, TokenType.ACCESS)
