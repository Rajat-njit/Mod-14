
# FastAPI Calculator — Full-Stack Web App with JWT Auth, BREAD Operations, Reporting, and CI/CD

[![FastAPI Calculator – CI/CD Pipeline](https://github.com/Rajat-njit/fastapi-calculator-final/actions/workflows/test.yml/badge.svg)](https://github.com/Rajat-njit/fastapi-calculator-final/actions/workflows/test.yml)

## 1) Project Summary

This project is a full-stack web application implemented with **FastAPI** (backend), **SQLAlchemy** (ORM), and a relational database (**PostgreSQL in CI / Docker**, SQLite optionally for local), with a browser-based UI rendered using **Jinja2 templates**.

The system supports:

* **Secure user registration and login**
* **JWT-based authentication and authorization**
* **Multiple calculation types** (basic + advanced arithmetic)
* **Persisting calculation history** per user
* **BREAD operations** on calculation resources (Browse, Read, Edit, Add, Delete)
* **Reporting / export features** (user statistics + CSV export)
* **Full test suite** (unit + integration + end-to-end via Playwright)
* **CI/CD pipeline** that runs tests, enforces coverage, security scanning, and deploys Docker image to Docker Hub

> **Note:** This README is intentionally detailed because it is used for grading and explains implementation decisions and rubric alignment.

---

## 📁 Project Structure

```text
module14_is601/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application entry point & route definitions
│   │
│   ├── core/                       # Global config & settings
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── database.py                 # SQLAlchemy engine & session setup
│   ├── database_init.py
│   │
│   ├── auth/                       # Security & Auth logic
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   └── dependencies.py
│   │
│   ├── models/                     # Database Models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── calculation.py
│   │
│   ├── schemas/                    # Pydantic Schemas (Data Validation)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── calculation.py
│   │   ├── token.py
│   │   └── stats.py
│   │
│   ├── services/                   # Business Logic Services
│   │   └── statistics_service.py
│   │
│   ├── operations/                 # Modular arithmetic logic
│   │   └── __init__.py
│   │
│   ├── static/                     # CSS/JS assets
│   └── templates/                  # Jinja2 HTML templates
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── .env.example
├── .github/
│   └── workflows/
│       └── test.yml
└── README.md
````

-----

## 📌 Folder Responsibilities

### 🔹 `app/main.py`

**Role: Application entry point**
Contains:

  * FastAPI app initialization
  * Route definitions (BREAD operations)
  * Dependency injection & Auth enforcement
  * CSV export & reporting endpoints
  * Lifespan events (DB initialization)

### 🔹 `app/core/`

**Role: Global configuration & environment management**

| File | Purpose |
| :--- | :--- |
| `config.py` | Loads environment variables, JWT secrets, expiry settings |

### 🔹 `app/database.py`

**Role: Database configuration**
Contains SQLAlchemy engine, SessionLocal, Declarative Base, and `get_db()` dependency. Used across routes, services, auth, and tests.

### 🔹 `app/auth/`

**Role: Security & authentication**

| File | Responsibility |
| :--- | :--- |
| `jwt.py` | Token creation, decoding, password hashing |
| `dependencies.py` | Auth guards & access control |

**Security Practices Implemented:**

  * bcrypt password hashing
  * JWT access & refresh tokens
  * Token type enforcement & expiration validation
  * Blacklist stubs (testable design)

### 🔹 `app/models/`

**Role: Database models & business logic**

  * **`user.py`**: User registration, authentication, password hashing, token verification.
  * **`calculation.py`**: Polymorphic calculation model, Factory pattern (`Calculation.create`). Supports: *Addition, Subtraction, Multiplication, Division, Exponentiation, Power, Modulus*.

### 🔹 `app/schemas/`

**Role: Data validation & API contracts (Pydantic v2)**

| Schema | Purpose |
| :--- | :--- |
| `base.py` | Shared validation logic |
| `user.py` | User create, login, update |
| `calculation.py` | Calculation request/response |
| `token.py` | Token response models |
| `stats.py` | Aggregated statistics |

### 🔹 `app/services/`

**Role: Reusable business services**

  * **`statistics_service.py`**: Computes user stats (total calculations, average operands, most-used operation, last timestamp).

-----

## ▶️ Running the Application Locally

### 1️⃣ Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd final_project
```

### 2️⃣ Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate    # macOS / Linux
# venv\Scripts\activate     # Windows
```

### 3️⃣ Install Dependencies

All required dependencies are listed and pinned in `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/fastapi_db
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/fastapi_test_db

JWT_SECRET_KEY=your_access_secret
JWT_REFRESH_SECRET_KEY=your_refresh_secret
ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

BCRYPT_ROUNDS=12
IS_TEST=false
```

### 5️⃣ Start the Application

```bash
uvicorn app.main:app --reload
```

Application will be available at:

  * **Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
  * **API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  * **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

-----

## 🧪 Running Tests Locally

This project follows a **layered testing strategy** (Unit → Integration → E2E).

### 🔹 Run Unit Tests (with Coverage Enforcement)

Enforces **≥90% backend coverage**, matching CI requirements.

```bash
pytest tests/unit \
  --cov=app \
  --cov-report=term-missing \
  --cov-fail-under=90
```

### 🔹 Run Integration Tests

Validates API routes and database interactions.

```bash
pytest tests/integration
```

### 🔹 Run End-to-End (E2E) Tests

Tests full user flows (login → dashboard → calculation → export).

```bash
playwright install
pytest tests/e2e
```

-----

## 🐳 Docker Hub Repository

The application is fully **Dockerized** and automatically built via **GitHub Actions**.

🔗 **Docker Hub Repository:** `https://hub.docker.com/r/<YOUR_DOCKERHUB_USERNAME>/fastapi-calculator`

**Pull and Run the Image:**

```bash
docker pull <YOUR_DOCKERHUB_USERNAME>/fastapi-calculator:latest
docker run -p 8000:8000 <YOUR_DOCKERHUB_USERNAME>/fastapi-calculator
```

-----

## 2\) Project Requirements Checklist

### ✅ Choose and Implement a New Feature

**Implemented: Report/History Feature**

  - [x] User calculation history stored in DB
  - [x] Usage statistics endpoint (`/calculations/stats`)
  - [x] CSV report export endpoint (`/calculations/export`)
  - [x] UI displays stats and supports download

**Additional Calculation Types:**

  - [x] Added **Exponentiation**, **Power**, **Modulus**

### ✅ Backend

  - [x] SQLAlchemy models for Users and Calculations
  - [x] Pydantic schemas for validation
  - [x] FastAPI routes for auth, calculations, and reporting
  - [x] Services layer for statistics aggregation

### ✅ Frontend

  - [x] Pages: Home, Register, Login, Dashboard, View, Edit
  - [x] Client-side behavior uses API & localStorage token persistence

### ✅ Testing

  - [x] **Unit tests:** Logic, utilities, models
  - [x] **Integration tests:** Routes, DB, Auth
  - [x] **E2E tests:** Playwright browser workflows

### ✅ CI/CD + Docker Deployment

  - [x] GitHub Actions pipeline (Install -\> Test -\> Coverage -\> Security Scan -\> Build -\> Push)

-----

## 3\) Key Features Implemented

### Authentication & Users

  * Secure password hashing (bcrypt via passlib).
  * JWT access + refresh token generation with active-user enforcement.
  * Token decoding, validation, and expiration handling.

### Calculations Engine

  * Polymorphic SQLAlchemy models with Factory method `Calculation.create()`.
  * Supports: Addition, Subtraction, Multiplication, Division, Exponentiation, Power, Modulus.

### BREAD Operations

**BREAD = Browse, Read, Edit, Add, Delete**
All actions are **user-scoped** (users only access their own records).

### Reporting & History

  * **Stats:** Total calculations, average operands, operation breakdown.
  * **Export:** CSV export via `StreamingResponse`.

-----

## 5\) High-Level Architecture

**Request Flow:**

1.  User registers/logs in → Backend generates **JWT**.
2.  UI stores tokens in `localStorage`.
3.  Requests sent with `Authorization: Bearer <token>`.
4.  **Dependencies:** Decode token, verify active user, scope queries to user ID.
5.  Results stored in DB; Statistics computed via service layer.

**Separation of Concerns:**

  * `models/`: Persistence + Business methods
  * `schemas/`: Validation + API shape
  * `services/`: Aggregation logic
  * `auth/`: Security helpers
  * `main.py`: Routes

-----

## 8\) API Design (BREAD Endpoints)

### 🧮 Calculation BREAD Endpoints

| BREAD | HTTP Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Add** | `POST` | `/calculations` | ✅ Yes | Create a new calculation and persist result |
| **Browse** | `GET` | `/calculations` | ✅ Yes | List all calculations for the logged-in user |
| **Read** | `GET` | `/calculations/{calc_id}` | ✅ Yes | Retrieve a specific calculation by ID |
| **Edit** | `PUT` | `/calculations/{calc_id}` | ✅ Yes | Update inputs and recompute result |
| **Delete** | `DELETE` | `/calculations/{calc_id}` | ✅ Yes | Delete a calculation owned by the user |

### 📊 Reporting & History Endpoints

| HTTP Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/calculations/stats` | ✅ Yes | Returns user calculation statistics and summaries |
| `GET` | `/calculations/export` | ✅ Yes | Export calculation history as CSV |
| `GET` | `/calculations/report.csv` | ✅ Yes | Alternate CSV export route |

-----

## 10\) Frontend Pages and Flow

| HTTP Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/` | Landing page |
| `GET` | `/login` | Login page |
| `GET` | `/register` | Registration page |
| `GET` | `/dashboard` | User dashboard (Stats + List) |
| `GET` | `/dashboard/view/{calc_id}` | View calculation |
| `GET` | `/dashboard/edit/{calc_id}` | Edit calculation |

-----

## 11\) Testing Strategy

This project follows a layered testing strategy aligned with industry best practices.

### 🧱 Testing Pyramid Overview

| Layer | Purpose | Scope |
| :--- | :--- | :--- |
| **Unit Tests** | Validate isolated logic | Models, services, schemas, utilities |
| **Integration Tests** | Validate API + DB interaction | Routes, auth, persistence |
| **E2E Tests** | Validate real user flows | UI + API + auth |

### 📌 Unit Test Coverage Map (`tests/unit/`)

| Test File | Covers | Application File |
| :--- | :--- | :--- |
| `test_calculator.py` | Basic arithmetic logic | `app/models/calculation.py` |
| `test_calculation_factory_unit.py` | Factory pattern mapping | `Calculation.create()` |
| `test_calculation_operations_unit.py` | Add/Sub/Mul/Div/Power/Modulus | Operation subclasses |
| `test_calculation_schema_unit.py` | Input validation | `app/schemas/calculation.py` |
| `test_dependencies_unit.py` | Auth dependency logic | `app/auth/dependencies.py` |
| `test_jwt_unit.py` | Token creation & decoding | `app/auth/jwt.py` |
| `test_user_unit.py` | User model behavior | `app/models/user.py` |
| `test_statistics_service_unit.py` | Stats computation | `compute_user_stats()` |

### 📌 Integration Test Coverage Map (`tests/integration/`)

| Test File | Covers | Application Area |
| :--- | :--- | :--- |
| `test_auth_routes.py` | Register + login routes | `/auth/*` |
| `test_calculation_routes.py` | CRUD calculations | `/calculations` |
| `test_api_new_operations.py` | Advanced ops (power, modulus) | Calculation extensions |
| `test_api_stats_and_report.py` | CSV + stats endpoints | Export & reporting |
| `test_database.py` | DB initialization | `database.py` |

### 📌 E2E Test Coverage Map (`tests/e2e/`)

| Test File | Covers | Scenario |
| :--- | :--- | :--- |
| `test_fastapi_calculator.py` | API + UI flow | Login → Calculate |
| `test_ui_playwright.py` | Browser automation | Full UI journey |

-----

## 14\) CI/CD Pipeline (`.github/workflows/test.yml`)

The CI pipeline is designed to satisfy both real-world best practices and professor requirements.

1.  **Test Job:**
      * Sets up Python & Dependencies.
      * Installs Playwright browsers.
      * Runs Unit Tests (**Enforces 90% Coverage**).
      * Runs Integration & E2E Tests.
2.  **Security Job:**
      * Runs **Trivy** scan on the Docker image.
3.  **Deploy Job:**
      * Builds & Pushes image to **Docker Hub** (on `main` branch).

-----

## 16\) Configuration: `.env` and `requirements.txt`

### `.env` File

Used for `DATABASE_URL`, `JWT_SECRET_KEY`, `BCRYPT_ROUNDS`, and `IS_TEST`.

### `requirements.txt`

Dependencies are pinned to ensure reproducibility. Key libraries include:

  * `fastapi`, `uvicorn`, `starlette` (Core)
  * `SQLAlchemy`, `psycopg2-binary` (DB)
  * `pydantic` (Validation)
  * `python-jose`, `passlib`, `bcrypt` (Auth)
  * `pytest`, `playwright`, `httpx` (Testing)

-----

# Conclusion

This project demonstrates an end-to-end FastAPI system including secure auth, DB-backed CRUD/BREAD resources, reporting implementation, frontend integration, thorough tests at multiple levels, CI/CD enforcement, and Docker deployment readiness.

----
## Author: Rajat Pednekar

```
```
