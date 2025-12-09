# tests/integration/test_api_new_operations.py

import pytest
from typing import Dict


def register_and_login(client, fake_user_data: Dict[str, str], password: str = "TestPass123!"):
    payload = {
        "first_name": fake_user_data["first_name"],
        "last_name": fake_user_data["last_name"],
        "email": fake_user_data["email"],
        "username": fake_user_data["username"],
        "password": password,
        "confirm_password": password,
    }

    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text

    login_payload = {
        "username": fake_user_data["username"],
        "password": password,
    }
    r2 = client.post("/auth/login", json=login_payload)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    return data["access_token"]


def test_exponentiation_operation(client, fake_user_data):
    """
    Ensure the exponentiation calculation works via API.
    Example: [2, 3] -> 2 ** 3 = 8
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"type": "exponentiation", "inputs": [2, 3]}
    resp = client.post("/calculations", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["type"] == "exponentiation"
    assert data["result"] == pytest.approx(8.0)


def test_power_operation(client, fake_user_data):
    """
    Ensure the power calculation (base ^ exponent) works via API.
    Example: [2, 4] -> 2 ** 4 = 16
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"type": "power", "inputs": [2, 4]}
    resp = client.post("/calculations", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["type"] == "power"
    assert data["result"] == pytest.approx(16.0)


def test_modulus_operation(client, fake_user_data):
    """
    Ensure the modulus calculation works via API.
    Example: [10, 3] -> 10 % 3 = 1
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"type": "modulus", "inputs": [10, 3]}
    resp = client.post("/calculations", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["type"] == "modulus"
    assert data["result"] == pytest.approx(1.0)


def test_modulus_requires_two_numbers(client, fake_user_data):
    """
    Modulus endpoint should return HTTP 400 when inputs length != 2.
    This checks our validation and error handling path.
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    # Only one operand -> invalid
    payload = {"type": "modulus", "inputs": [10]}
    resp = client.post("/calculations", json=payload, headers=headers)

    assert resp.status_code == 400
    data = resp.json()
    # Error message comes from the ValueError in Modulus.get_result()
    assert "Modulus operation requires exactly two numbers" in data.get("detail", "")
