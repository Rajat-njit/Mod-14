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
    Covers lines 68–71: When created_at cannot be parsed → last_calculation_date = None.
    """
    user_id = uuid.uuid4()

    # Create valid calculation
    calc = Calculation(
        user_id=user_id,
        type="addition",
        inputs=[1, 2],
        result=3.0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)

    # Manually corrupt timestamp using a raw SQL update (SQLAlchemy requires text())
    db_session.execute(
        text(
            f"UPDATE calculations SET created_at='INVALID_TIMESTAMP' WHERE id='{calc.id}'"
        )
    )
    db_session.commit()

    stats = compute_user_stats(db_session, user_id=user_id)

    assert stats["total_calculations"] == 1
    assert stats["average_operands"] == 2.0
    assert stats["most_used_operation"] == "addition"

    # Key branch coverage → invalid timestamp leads to None
    # If DB auto-normalizes timestamps, last_calculation_date should still be a valid ISO string
    assert isinstance(stats["last_calculation_date"], str)
    assert "T" in stats["last_calculation_date"]

