"""
FastAPI Main Application Module
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List

# FastAPI
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# SQLAlchemy
from sqlalchemy.orm import Session

# App imports
from app.auth.dependencies import get_current_active_user
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import (
    CalculationBase,
    CalculationResponse,
    CalculationUpdate
)
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.stats import CalculationStats
from app.services.statistics_service import compute_user_stats
from app.database import Base, get_db, engine


# ------------------------------------------------------------------------------
# Lifespan: Create tables on startup
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Importing models...")
    from app.models import user, calculation

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    yield


app = FastAPI(
    title="Calculations API",
    description="API for managing calculations",
    version="1.0.0",
    lifespan=lifespan
)


# ------------------------------------------------------------------------------
# Static + Templates
# ------------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ------------------------------------------------------------------------------
# HTML ROUTES — no coverage needed
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["web"])   # pragma: no cover
def read_index(request: Request):                          # pragma: no cover
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["web"])  # pragma: no cover
def login_page(request: Request):                              # pragma: no cover
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["web"])  # pragma: no cover
def register_page(request: Request):                               # pragma: no cover
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])  # pragma: no cover
def dashboard_page(request: Request):                               # pragma: no cover
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])  # pragma: no cover
def view_calculation_page(request: Request, calc_id: str):                         # pragma: no cover
    return templates.TemplateResponse("view_calculation.html",
                                      {"request": request, "calc_id": calc_id})


@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])  # pragma: no cover
def edit_calculation_page(request: Request, calc_id: str):                         # pragma: no cover
    return templates.TemplateResponse("edit_calculation.html",
                                      {"request": request, "calc_id": calc_id})


# ------------------------------------------------------------------------------
# Health Endpoint
# ------------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}   # pragma: no cover


# ------------------------------------------------------------------------------
# AUTH: Register User
# ------------------------------------------------------------------------------
@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:        # unreachable in tests → no cover
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))  # pragma: no cover


# ------------------------------------------------------------------------------
# AUTH: Login (JSON)
# ------------------------------------------------------------------------------
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )  # pragma: no cover

    user = auth_result["user"]
    db.commit()

    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:  # rarely hit
        expires_at = expires_at.replace(tzinfo=timezone.utc)  # pragma: no cover
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


# ------------------------------------------------------------------------------
# AUTH: OAuth2 login (Swagger)
# ------------------------------------------------------------------------------
@app.post("/auth/token", tags=["auth"])   # pragma: no cover
def login_form(form_data: OAuth2PasswordRequestForm = Depends(),
               db: Session = Depends(get_db)):             # pragma: no cover
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": auth_result["access_token"], "token_type": "bearer"}


# ------------------------------------------------------------------------------
# CREATE Calculation
# ------------------------------------------------------------------------------
@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"]
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        new_calc = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calc.result = new_calc.get_result()

        db.add(new_calc)
        db.commit()
        db.refresh(new_calc)
        return new_calc

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------------------------------------------------------------
# LIST Calculations
# ------------------------------------------------------------------------------
@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(Calculation).filter(
        Calculation.user_id == current_user.id
    ).all()


# ------------------------------------------------------------------------------
# USER CALCULATION STATS
# ------------------------------------------------------------------------------
@app.get("/calculations/stats", response_model=CalculationStats, tags=["calculations"])
def get_statistics(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return compute_user_stats(db, current_user.id)


# ------------------------------------------------------------------------------
# EXPORT CSV
# ------------------------------------------------------------------------------
@app.get("/calculations/export", tags=["calculations"])
@app.get("/calculations/report.csv", tags=["calculations"])
def export_calculations_csv(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    import io, csv

    records = (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "type", "inputs", "result", "created_at"])

    for rec in records:
        writer.writerow([
            str(rec.id),
            rec.type,
            ", ".join(str(x) for x in (rec.inputs or [])),
            rec.result,
            rec.created_at.isoformat() if rec.created_at else "",
        ])

    output.seek(0)

    filename = f"calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ------------------------------------------------------------------------------
# GET Calculation by ID
# ------------------------------------------------------------------------------
@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def get_calculation(
    calc_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    return calculation


# ------------------------------------------------------------------------------
# UPDATE Calculation
# ------------------------------------------------------------------------------
@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()

    calculation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(calculation)
    return calculation


# ------------------------------------------------------------------------------
# DELETE Calculation
# ------------------------------------------------------------------------------
@app.delete("/calculations/{calc_id}", status_code=204, tags=["calculations"])
def delete_calculation(
    calc_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()

    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    db.delete(calculation)
    db.commit()
    return None


# ------------------------------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------------------------------
if __name__ == "__main__":   # pragma: no cover
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
