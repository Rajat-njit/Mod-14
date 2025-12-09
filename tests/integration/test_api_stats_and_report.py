# tests/integration/test_api_stats_and_report.py

import pytest
from typing import Dict

from app.schemas.stats import CalculationStats


def register_and_login(client, fake_user_data: Dict[str, str], password: str = "TestPass123!"):
    """
    Helper: register a new user via API and login to get a Bearer token.
    """
    payload = {
        "first_name": fake_user_data["first_name"],
        "last_name": fake_user_data["last_name"],
        "email": fake_user_data["email"],
        "username": fake_user_data["username"],
        "password": password,
        "confirm_password": password,
    }

    # Register user
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text

    # Login
    login_payload = {
        "username": fake_user_data["username"],
        "password": password,
    }
    resp_login = client.post("/auth/login", json=login_payload)
    assert resp_login.status_code == 200, resp_login.text

    data = resp_login.json()
    assert "access_token" in data
    return data["access_token"]


def test_stats_initial_empty(client, fake_user_data):
    """
    When a new user has no calculations, the stats endpoint should return zeros
    and an empty breakdown.
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/calculations/stats", headers=headers)
    assert resp.status_code == 200, resp.text

    stats = CalculationStats(**resp.json())

    assert stats.total_calculations == 0
    assert stats.average_operands == 0.0
    assert stats.operations_breakdown == {}
    assert stats.most_used_operation is None
    assert stats.last_calculation_date is None


def test_stats_after_creating_calculations(client, fake_user_data):
    """
    After creating several calculations via API, the stats endpoint should
    reflect totals, averages, and breakdown correctly.
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    # Create several calculations of different types
    payloads = [
        {"type": "addition", "inputs": [1, 2]},
        {"type": "subtraction", "inputs": [10, 3]},
        {"type": "multiplication", "inputs": [2, 3, 4]},
        {"type": "power", "inputs": [2, 3]},
    ]

    for p in payloads:
        r = client.post("/calculations", json=p, headers=headers)
        assert r.status_code == 201, r.text

    # Fetch stats
    resp = client.get("/calculations/stats", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    stats = CalculationStats(**data)

    # There should be 4 calculations total
    assert stats.total_calculations == len(payloads)

    # Average operands should be reasonable (~ 2–3), use approx
    assert stats.average_operands == pytest.approx( (2 + 2 + 3 + 2) / 4 )

    # Breakdown should contain our operation types
    for op_type in ["addition", "subtraction", "multiplication", "power"]:
        assert op_type in stats.operations_breakdown
        assert stats.operations_breakdown[op_type] >= 1

    # Most used operation should be one of the keys (we don't require exact)
    if stats.most_used_operation is not None:
        assert stats.most_used_operation in stats.operations_breakdown

    # Last calculation date should be a non-empty string
    assert isinstance(stats.last_calculation_date, str)
    assert stats.last_calculation_date != ""


def test_download_report_csv(client, fake_user_data):
    """
    Verify that the CSV report endpoint returns a CSV file with header and rows
    for the current user's calculations.
    """
    token = register_and_login(client, fake_user_data)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a couple of calculations
    payloads = [
        {"type": "addition", "inputs": [5, 10]},
        {"type": "division", "inputs": [100, 5]},
    ]

    for p in payloads:
        r = client.post("/calculations", json=p, headers=headers)
        assert r.status_code == 201, r.text

    # Hit CSV endpoint (we assume route path: /calculations/report.csv)
    resp = client.get("/calculations/report.csv", headers=headers)
    assert resp.status_code == 200, resp.text

    # Content-Type should be CSV-ish
    content_type = resp.headers.get("content-type", "")
    assert "text/csv" in content_type or "application/octet-stream" in content_type

    body = resp.text
    lines = [line for line in body.splitlines() if line.strip()]

    # At least header + one data row
    assert len(lines) >= 2

    header = lines[0].split(",")
    # Check that important columns exist
    for col in ["id", "type", "inputs", "result", "created_at"]:
        assert col in header
