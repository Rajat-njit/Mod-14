import pytest
from uuid import uuid4
from fastapi import HTTPException

from app.auth.jwt import create_token, decode_token
from app.schemas.token import TokenType


@pytest.mark.asyncio
async def test_decode_token_invalid_signature():
    token = create_token(uuid4(), TokenType.ACCESS)
    tampered = token + "broken"

    with pytest.raises(HTTPException) as exc:
        await decode_token(tampered, TokenType.ACCESS)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_decode_token_wrong_type():
    token = create_token(uuid4(), TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await decode_token(token, TokenType.REFRESH)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_decode_token_revoked(monkeypatch):
    async def fake_blacklisted(jti):
        return True

    monkeypatch.setattr("app.auth.jwt.is_blacklisted", fake_blacklisted)

    token = create_token(uuid4(), TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await decode_token(token, TokenType.ACCESS)

    assert exc.value.status_code == 401
