import pytest
import uuid
from fastapi import status
from app.models.user import User


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def valid_password():
    # Must meet your schema's requirements:
    # - ≥ 8 chars
    # - uppercase
    # - lowercase
    # - digit
    # - special char
    return "StrongPass123!"


# ---------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------

def test_register_success(client):
    payload = {
        "first_name": "Alice",
        "last_name": "Wonder",
        "email": f"alice_{uuid.uuid4().hex[:6]}@example.com",
        "username": f"alice_{uuid.uuid4().hex[:6]}",
        "password": valid_password(),
        "confirm_password": valid_password(),
    }

    resp = client.post("/auth/register", json=payload)

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]


def test_register_duplicate_user(client, db_session):
    """Register user twice → second attempt should return 400."""
    email = f"dupe_{uuid.uuid4().hex[:6]}@example.com"
    username = f"dupe_{uuid.uuid4().hex[:6]}"

    payload = {
        "first_name": "Dup",
        "last_name": "User",
        "email": email,
        "username": username,
        "password": valid_password(),
        "confirm_password": valid_password(),
    }

    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second attempt should fail with HTTP 400 (business rule)
    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "exists" in resp2.json()["detail"]


def test_register_invalid_password(client):
    """
    INVALID PASSWORD TEST:
    Your schema enforces strict validation at the Pydantic level.
    A weak password causes a 422 (schema validation error).
    """
    payload = {
        "first_name": "Weak",
        "last_name": "Password",
        "email": f"weak_{uuid.uuid4().hex[:6]}@example.com",
        "username": f"weak_{uuid.uuid4().hex[:6]}",
        "password": "weakpass",             # Missing uppercase, digit, special
        "confirm_password": "weakpass",
    }

    resp = client.post("/auth/register", json=payload)

    # Strict schema → 422 expected
    assert resp.status_code == 422
    assert "Password must contain at least one uppercase letter" in resp.text \
        or "Password must contain at least one digit" in resp.text \
        or "Password must contain at least one special character" in resp.text


# ---------------------------------------------------------
# Login Tests
# ---------------------------------------------------------

def test_login_success(client, db_session):
    """Successful login with correct credentials."""
    email = f"login_{uuid.uuid4().hex[:6]}@example.com"
    username = f"login_{uuid.uuid4().hex[:6]}"

    user = User(
        first_name="Log",
        last_name="In",
        email=email,
        username=username,
        hashed_password=User.hash_password(valid_password()),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/login", json={
        "username": username,
        "password": valid_password()
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user_id"] == str(user.id)


def test_login_invalid_credentials(client):
    """Attempt login with wrong password → 401 expected."""
    resp = client.post("/auth/login", json={
        "username": "nonexistent_user",
        "password": valid_password()
    })

    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]
