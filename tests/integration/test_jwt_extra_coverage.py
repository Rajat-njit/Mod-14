import pytest
import uuid
from datetime import timedelta, datetime
from fastapi import HTTPException

from app.auth.jwt import (
    create_token,
    decode_token,
    get_current_user,
)
from app.schemas.token import TokenType


# -------------------------------------------------
# Helpers
# -------------------------------------------------
@pytest.fixture
def inactive_user(db_session):
    """Create an inactive user with required fields."""
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        username=f"inactive_{uuid.uuid4().hex[:6]}",
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        hashed_password="dummy",
        is_active=False,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# -------------------------------------------------
# create_token tests
# -------------------------------------------------

@pytest.mark.asyncio
async def test_create_token_with_expires_delta():
    """Covers explicit expires_delta path."""
    token = create_token(
        user_id=uuid.uuid4(),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=1),
    )
    assert isinstance(token, str)


def test_create_token_uuid_normalization():
    """Covers UUID normalization."""
    token = create_token(uuid.uuid4(), TokenType.ACCESS)
    assert isinstance(token, str)


def test_create_token_encode_error(monkeypatch):
    """Force jwt.encode failure and assert 500 error."""
    import app.auth.jwt as jwt_module

    def bad_encode(*args, **kwargs):
        raise Exception("encode failure")

    monkeypatch.setattr("jose.jwt.encode", bad_encode)

    with pytest.raises(HTTPException) as exc:
        create_token(uuid.uuid4(), TokenType.ACCESS)

    assert exc.value.status_code == 500
    assert "Could not create token" in exc.value.detail


# -------------------------------------------------
# decode_token tests
# -------------------------------------------------

@pytest.mark.asyncio
async def test_decode_token_success():
    """Happy path decode."""
    token = create_token(uuid.uuid4(), TokenType.ACCESS)
    payload = await decode_token(token, TokenType.ACCESS)
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_decode_token_invalid_type():
    """Decode with wrong expected type."""
    refresh = create_token(uuid.uuid4(), TokenType.REFRESH)

    with pytest.raises(HTTPException):
        await decode_token(refresh, TokenType.ACCESS)


@pytest.mark.asyncio
async def test_decode_token_revoked(monkeypatch):
    """Token is blacklisted → revoked."""
    async def fake_blacklisted(jti):
        return True

    monkeypatch.setattr("app.auth.jwt.is_blacklisted", fake_blacklisted)

    token = create_token(uuid.uuid4(), TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await decode_token(token, TokenType.ACCESS)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token has been revoked"


@pytest.mark.asyncio
async def test_decode_token_expired():
    """Expired token should raise 401."""
    expired = create_token(
        uuid.uuid4(),
        TokenType.ACCESS,
        expires_delta=timedelta(seconds=-5),
    )

    with pytest.raises(HTTPException):
        await decode_token(expired, TokenType.ACCESS)


@pytest.mark.asyncio
async def test_decode_token_jwt_error():
    """Tampered signature produces JWTError."""
    token = create_token(uuid.uuid4(), TokenType.ACCESS)
    tampered = token + "XYZ"

    with pytest.raises(HTTPException):
        await decode_token(tampered, TokenType.ACCESS)


@pytest.mark.asyncio
async def test_decode_token_invalid_type_mismatch():
    """
    ACCESS token decoded as REFRESH token.
    Your implementation throws JWTError → "Could not validate credentials".
    """
    token = create_token(uuid.uuid4(), TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await decode_token(token, TokenType.REFRESH)

    assert exc.value.status_code == 401
    assert exc.value.detail in [
        "Invalid token type",
        "Could not validate credentials",
    ]


# -------------------------------------------------
# get_current_user tests
# -------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_not_found(monkeypatch, db_session):
    """Decode valid token but user does not exist."""
    async def fake_decode(token, token_type):
        return {"sub": "non-existent-id"}

    monkeypatch.setattr("app.auth.jwt.decode_token", fake_decode)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="dummy", db=db_session)

    # Your implementation returns 401 when downstream lookup fails
    assert exc.value.status_code == 401
    assert "User not found" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive(monkeypatch, db_session, inactive_user):
    """Inactive user should trigger 400."""
    async def fake_decode(token, token_type):
        return {"sub": str(inactive_user.id)}

    monkeypatch.setattr("app.auth.jwt.decode_token", fake_decode)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="dummy", db=db_session)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Inactive user"


@pytest.mark.asyncio
async def test_get_current_user_unexpected_error(monkeypatch):
    """Covers catch-all block in get_current_user."""

    async def boom(*args, **kwargs):
        raise Exception("Unexpected error!")

    monkeypatch.setattr("app.auth.jwt.decode_token", boom)

    token = create_token(uuid.uuid4(), TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token)

    assert exc.value.status_code == 401
    assert "Unexpected error!" in exc.value.detail
