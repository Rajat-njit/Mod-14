# tests/integration/test_calculation_routes.py

import uuid
import pytest
from fastapi import status
from app.models.user import User


@pytest.fixture
def auth_headers(db_session, client):
    """Create a unique user for EACH test and return Authorization headers."""

    user_data = {
        "first_name": "Calc",
        "last_name": "Tester",
        "email": f"calc_{uuid.uuid4().hex}@example.com",   # UNIQUE email
        "username": f"calcuser_{uuid.uuid4().hex}",        # UNIQUE username
        "password": "StrongPass123",
    }

    user = User.register(db_session, user_data)
    db_session.commit()
    db_session.refresh(user)

    # login to get token
    response = client.post(
        "/auth/login",
        json={"username": user.username, "password": "StrongPass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}



# ------------------------------------------------------------
# CREATE calculation
# ------------------------------------------------------------
def test_create_calculation(client, auth_headers):
    payload = {
        "type": "addition",
        "inputs": [3, 4]
    }

    resp = client.post("/calculations", json=payload, headers=auth_headers)
    assert resp.status_code == status.HTTP_201_CREATED

    data = resp.json()
    assert data["type"] == "addition"
    assert data["result"] == 7
    assert len(data["inputs"]) == 2


# ------------------------------------------------------------
# LIST calculations
# ------------------------------------------------------------
def test_list_calculations(client, auth_headers):
    # create 1
    client.post("/calculations", json={
        "type": "addition",
        "inputs": [1, 2]
    }, headers=auth_headers)

    # list
    resp = client.get("/calculations", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


# ------------------------------------------------------------
# GET calculation by ID
# ------------------------------------------------------------
def test_get_calculation(client, auth_headers):
    create = client.post("/calculations", json={
        "type": "subtraction",
        "inputs": [10, 3]
    }, headers=auth_headers)

    calc_id = create.json()["id"]

    resp = client.get(f"/calculations/{calc_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["result"] == 7


def test_get_calculation_invalid_uuid(client, auth_headers):
    resp = client.get("/calculations/not-a-uuid", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid calculation id format."


def test_get_calculation_not_found(client, auth_headers):
    random_id = uuid.uuid4()
    resp = client.get(f"/calculations/{random_id}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Calculation not found."


# ------------------------------------------------------------
# UPDATE calculation
# ------------------------------------------------------------
def test_update_calculation(client, auth_headers):
    create = client.post("/calculations", json={
        "type": "multiplication",
        "inputs": [2, 5]
    }, headers=auth_headers)

    calc_id = create.json()["id"]

    update = client.put(f"/calculations/{calc_id}", json={
        "inputs": [3, 3]
    }, headers=auth_headers)

    assert update.status_code == 200
    assert update.json()["result"] == 9


def test_update_calculation_invalid_id(client, auth_headers):
    resp = client.put("/calculations/not-a-uuid",
                      json={"inputs": [1, 2]},
                      headers=auth_headers)
    assert resp.status_code == 400


def test_update_calculation_not_found(client, auth_headers):
    resp = client.put(f"/calculations/{uuid.uuid4()}",
                      json={"inputs": [1, 2]},
                      headers=auth_headers)
    assert resp.status_code == 404


# ------------------------------------------------------------
# DELETE calculation
# ------------------------------------------------------------
def test_delete_calculation(client, auth_headers):
    create = client.post("/calculations", json={
        "type": "division",
        "inputs": [20, 2]
    }, headers=auth_headers)

    calc_id = create.json()["id"]

    resp = client.delete(f"/calculations/{calc_id}", headers=auth_headers)
    assert resp.status_code == 204

    # confirm deletion
    resp2 = client.get(f"/calculations/{calc_id}", headers=auth_headers)
    assert resp2.status_code == 404


# ------------------------------------------------------------
# STATS endpoint
# ------------------------------------------------------------
def test_calculation_stats(client, auth_headers):
    # Create a calculation
    client.post(
        "/calculations",
        json={"type": "addition", "inputs": [10, 5]},
        headers=auth_headers
    )

    # Hit stats endpoint
    resp = client.get("/calculations/stats", headers=auth_headers)
    assert resp.status_code == 200

    data = resp.json()

    # Validate real fields actually returned by your API
    assert "operations_breakdown" in data
    assert "most_used_operation" in data
    assert "average_operands" in data
    assert "last_calculation_date" in data

    # Verify expected values
    assert data["most_used_operation"] == "addition"
    assert data["operations_breakdown"].get("addition") == 1
    assert data["average_operands"] == 2.0



# ------------------------------------------------------------
# CSV EXPORT endpoint
# ------------------------------------------------------------
def test_export_calculations_csv(client, auth_headers):
    client.post("/calculations", json={
        "type": "addition",
        "inputs": [4, 6]
    }, headers=auth_headers)

    resp = client.get("/calculations/export", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert "attachment; filename=" in resp.headers["Content-Disposition"]

    assert "addition" in resp.text
    assert "4.0, 6.0" in resp.text

