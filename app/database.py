# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# ----------------------------------------------------------
# ENGINE SELECTION BASED ON ENVIRONMENT
# ----------------------------------------------------------

def get_engine(database_url: str | None = None):
    """Return an engine using DATABASE_URL or a provided override."""
    url = database_url or settings.DATABASE_URL

    # SQLite needs special connect args
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
    return create_engine(url)


def get_sessionmaker(engine):
    """Return a sessionmaker bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create main engine depending on IS_TEST flag
engine = get_engine()

# SessionLocal bound to the selected engine (Postgres or SQLite)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()


# ----------------------------------------------------------
# DATABASE SESSION DEPENDENCY
# ----------------------------------------------------------

def get_db():
    """Provide a database session for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------
# MODEL INITIALIZATION FUNCTION
# ----------------------------------------------------------

def init_models():
    """
    Import models AFTER Base is defined so SQLAlchemy
    becomes aware of them.
    """
    from app.models.user import User
    from app.models.calculation import Calculation
