import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import text

from app.services.statistics_service import compute_user_stats
from app.models.calculation import Calculation


def test_stats_invalid_user_id_string_returns_empty(db_session):
    """Covers invalid UUID fallback logic."""
    stats = compute_user_stats(db_session, user_id="NOT_A_REAL_UUID")

    assert stats["total_calculations"] == 0
    assert stats["average_operands"] == 0.0
    assert stats["operations_breakdown"] == {}
    assert stats["most_used_operation"] is None
    assert stats["last_calculation_date"] is None


def test_stats_invalid_timestamp_handling(db_session):
    """
    Basic sanity check on last_calculation_date formatting.
    Ensures we get a valid ISO 8601 string for the user's last calculation.
    """
    from app.models.user import User

    # 1. Create a real user to satisfy FK constraint in Postgres
    user = User(
        id=uuid.uuid4(),
        username=f"user_{uuid.uuid4().hex[:6]}",
        email="stats@example.com",
        hashed_password="dummy",
        first_name="Stats",
        last_name="User",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2. Create a valid calculation for that user
    calc = Calculation(
        user_id=user.id,
        type="addition",
        inputs=[1, 2],
        result=3.0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)

    # 3. Compute stats
    stats = compute_user_stats(db_session, user_id=user.id)

    assert stats["total_calculations"] == 1
    assert stats["average_operands"] == 2.0
    assert stats["most_used_operation"] == "addition"
    assert isinstance(stats["last_calculation_date"], str)
    assert "T" in stats["last_calculation_date"]
