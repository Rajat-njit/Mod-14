# tests/e2e/test_ui_playwright.py

from uuid import uuid4
from datetime import datetime, timezone

import requests
from playwright.sync_api import Page, expect


def _base_url(fastapi_server: str) -> str:
    """Normalize base URL (no trailing slash)."""
    return fastapi_server.rstrip("/")


# ---------------------------------------------------------------------------
# Helpers: create user + login via API (to seed UI tests cleanly)
# ---------------------------------------------------------------------------

def _register_user_via_api(base_url: str, username: str, email: str, password: str) -> None:
    payload = {
        "first_name": "UITest",
        "last_name": "User",
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password,
    }
    resp = requests.post(f"{base_url}/auth/register", json=payload)
    # 201 on first create, 400 if duplicated (fine for tests that reuse username)
    assert resp.status_code in (201, 400), f"Register API failed: {resp.status_code} {resp.text}"


def _login_user_via_api(base_url: str, username: str, password: str) -> dict:
    payload = {"username": username, "password": password}
    resp = requests.post(f"{base_url}/auth/login", json=payload)
    assert resp.status_code == 200, f"Login API failed: {resp.status_code} {resp.text}"
    return resp.json()


def _seed_logged_in_local_storage(page: Page, base_url: str, username: str, password: str) -> dict:
    """
    Create a user (if needed), login via API, then stuff the tokens into
    window.localStorage so the dashboard JS sees an authenticated session.
    """
    _register_user_via_api(base_url, username, f"{username}@example.com", password)
    tokens = _login_user_via_api(base_url, username, password)

    # Navigate once to establish origin, then set localStorage
    page.goto(base_url)
    page.evaluate(
        """
        (tokenData) => {
            localStorage.setItem('access_token', tokenData.access_token);
            localStorage.setItem('refresh_token', tokenData.refresh_token);
            localStorage.setItem('token_expires', tokenData.expires_at);
            localStorage.setItem('user_id', tokenData.user_id);
            localStorage.setItem('username', tokenData.username);
        }
        """,
        tokens,
    )
    return tokens


# ---------------------------------------------------------------------------
# 1) Home page – navigation + hero content
# ---------------------------------------------------------------------------

def test_home_page_has_title_and_auth_links(page: Page, fastapi_server: str):
    base = _base_url(fastapi_server)
    page.goto(f"{base}/")

    # Main hero heading from index.html
    expect(page.get_by_role("heading", name="Welcome to the Calculations App")).to_be_visible()

    # Top-level Login / Register links (could be in nav or hero CTA)
    login_link = page.get_by_role("link", name="Login").first
    register_link = page.get_by_role("link", name="Register").first

    expect(login_link).to_be_visible()
    expect(register_link).to_be_visible()

    # Basic href sanity
    assert "/login" in (login_link.get_attribute("href") or "")
    assert "/register" in (register_link.get_attribute("href") or "")


# ---------------------------------------------------------------------------
# 2) Register page – client-side validation + success flow
# ---------------------------------------------------------------------------

def test_register_page_password_mismatch_shows_error(page: Page, fastapi_server: str):
    """
    Client-side validation:
    - Fill valid username/email
    - Intentionally mismatch password/confirm_password
    - Expect password mismatch error + red styling
    """
    base = _base_url(fastapi_server)
    page.goto(f"{base}/register")

    username = f"ui_reg_mismatch_{uuid4().hex[:6]}"
    email = f"{username}@example.com"

    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#first_name", "Mismatch")
    page.fill("#last_name", "Test")
    page.fill("#password", "StrongPass123")
    page.fill("#confirm_password", "StrongPass1234")  # mismatch

    page.click("button[type='submit']")

    error_alert = page.locator("#errorAlert")
    match_error = page.locator("#passwordMatchError")

    expect(error_alert).to_be_visible()
    expect(error_alert).to_contain_text("Passwords do not match")
    expect(match_error).to_be_visible()


def test_register_success_redirects_to_login(page: Page, fastapi_server: str):
    """
    Full happy-path registration through the UI:
    - Fill all fields with a strong password
    - Submit
    - Expect success alert
    - Then redirect to /login (JS setTimeout in register.html)
    """
    base = _base_url(fastapi_server)
    page.goto(f"{base}/register")

    username = f"ui_reg_ok_{uuid4().hex[:6]}"
    email = f"{username}@example.com"
    password = "StrongPass123!"

    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#first_name", "Alice")
    page.fill("#last_name", "UI")
    page.fill("#password", password)
    page.fill("#confirm_password", password)

    page.click("button[type='submit']")

    success_alert = page.locator("#successAlert")
    expect(success_alert).to_be_visible()
    expect(success_alert).to_contain_text("Registration successful")

    # Register JS does a 2s delay before redirect → login
    page.wait_for_url("**/login", timeout=6000)


# ---------------------------------------------------------------------------
# 3) Login page – invalid + valid flows
# ---------------------------------------------------------------------------

def test_login_invalid_credentials_show_error(page: Page, fastapi_server: str):
    base = _base_url(fastapi_server)
    page.goto(f"{base}/login")

    page.fill("#username", "nonexistent_user")
    page.fill("#password", "WrongPass123!")

    page.click("button[type='submit']")

    error_alert = page.locator("#errorAlert")
    expect(error_alert).to_be_visible()
    expect(error_alert).to_contain_text("Invalid username or password")



def test_login_success_stores_tokens_and_redirects_to_dashboard(page: Page, fastapi_server: str):
    """
    Full login UI flow:
    - Pre-create user via API
    - Login via /login page
    - Check redirect to /dashboard
    - Check localStorage has access_token + username
    """
    base = _base_url(fastapi_server)
    username = f"ui_login_ok_{uuid4().hex[:6]}"
    password = "StrongPass123!"
    email = f"{username}@example.com"

    # Seed user via API
    _register_user_via_api(base, username, email, password)

    # Now login via UI
    page.goto(f"{base}/login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("button[type='submit']")

    # Expect redirect to dashboard
    page.wait_for_url("**/dashboard", timeout=6000)

    # Check that dashboard heading exists
    expect(page.get_by_role("heading", name="New Calculation")).to_be_visible()

    # Verify localStorage tokens
    access_token = page.evaluate("() => window.localStorage.getItem('access_token')")
    stored_username = page.evaluate("() => window.localStorage.getItem('username')")

    assert access_token is not None and len(access_token) > 0
    assert stored_username == username


# ---------------------------------------------------------------------------
# 4) Dashboard access control
# ---------------------------------------------------------------------------

def test_dashboard_redirects_to_login_without_token(page: Page, fastapi_server: str):
    """
    If there is no access_token in localStorage, dashboard JS should redirect
    back to /login.
    """
    base = _base_url(fastapi_server)

    # Ensure no residual storage
    page.goto(base)
    page.evaluate("() => { localStorage.clear(); }")

    page.goto(f"{base}/dashboard")
    page.wait_for_url("**/login", timeout=6000)


# ---------------------------------------------------------------------------
# 5) Dashboard – new calculation flow + table + stats
# ---------------------------------------------------------------------------

def test_dashboard_new_calculation_updates_history_and_stats(page: Page, fastapi_server: str):
    """
    Most important UI E2E:
    - Seed logged-in user via API (tokens in localStorage)
    - Visit /dashboard
    - Submit a new multiplication calculation
    - Expect success alert
    - Expect new row in history with correct result
    """
    base = _base_url(fastapi_server)
    username = f"ui_dash_calc_{uuid4().hex[:6]}"
    password = "StrongPass123!"

    _seed_logged_in_local_storage(page, base, username, password)

    page.goto(f"{base}/dashboard")

    # Ensure dashboard shell is visible
    expect(page.get_by_role("heading", name="New Calculation")).to_be_visible()

    # Fill new calculation form
    page.select_option("#calcType", "multiplication")
    page.fill("#calcInputs", "2, 3, 4")
    page.click("button[type='submit']")

    # Success alert
    success_alert = page.locator("#successAlert")
    expect(success_alert).to_be_visible()
    expect(success_alert).to_contain_text("Calculation complete")

    # History table should have at least one row with 24 as result
    table_body = page.locator("#calculationsTable")
    expect(table_body).to_be_visible()

    # Wait for at least one data row (skip the loading row)
    expect(table_body.locator("tr")).to_have_count(1, timeout=6000)

    # Assert that some cell contains "24"
    expect(table_body).to_contain_text("24")

    # Stats panel should show a "Total Calculations" card
    stats_panel = page.locator("#statsPanel")
    expect(stats_panel).to_be_visible()
    expect(stats_panel).to_contain_text("Total Calculations")


# ---------------------------------------------------------------------------
# 6) Dashboard – CSV download button triggers a download
# ---------------------------------------------------------------------------

def test_dashboard_download_csv_triggers_download(page: Page, fastapi_server: str):
    """
    Smoke test for CSV export from the UI:
    - Seed user + login via API
    - Ensure at least one calculation exists (via API)
    - Click "Download CSV" button
    - Expect a browser download event
    """
    base = _base_url(fastapi_server)
    username = f"ui_csv_{uuid4().hex[:6]}"
    password = "StrongPass123!"

    tokens = _seed_logged_in_local_storage(page, base, username, password)

    # Create at least one calculation via API so the CSV isn't empty
    api_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    calc_payload = {"type": "addition", "inputs": [1, 2, 3]}
    resp = requests.post(f"{base}/calculations", json=calc_payload, headers=api_headers)
    assert resp.status_code == 201, f"Failed to seed calculation: {resp.status_code} {resp.text}"

    # Now hit dashboard and click Download CSV
    page.goto(f"{base}/dashboard")
    download_button = page.locator("#downloadCsvBtn")
    expect(download_button).to_be_visible()

    with page.expect_download() as download_info:
        download_button.click()

    download = download_info.value
    # We just assert that *a* CSV-like file was generated
    suggested_name = download.suggested_filename
    assert suggested_name.endswith(".csv") or "calculation" in suggested_name.lower()
