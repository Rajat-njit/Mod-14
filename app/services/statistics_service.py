# app/services/statistics_service.py

from sqlalchemy.orm import Session
from app.models.calculation import Calculation
from collections import Counter
from datetime import datetime
from uuid import UUID


def compute_user_stats(db: Session, user_id):
    """
    Compute statistics for all calculations belonging to a given user.
    Works with both UUID objects and UUID strings.
    """

    # --- FIX 1: Normalize user_id to UUID for SQLAlchemy (SQLite+Postgres safe) ---
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except Exception:
            # If somehow not a valid UUID, return empty stats
            return {
                "total_calculations": 0,
                "average_operands": 0.0,
                "operations_breakdown": {},
                "most_used_operation": None,
                "last_calculation_date": None,
            }

    # --- Query calculations ---
    records = (
        db.query(Calculation)
        .filter(Calculation.user_id == user_id)
        .all()
    )

    # If no calculations exist
    if not records:
        return {
            "total_calculations": 0,
            "average_operands": 0.0,
            "operations_breakdown": {},
            "most_used_operation": None,
            "last_calculation_date": None,
        }

    total = len(records)

    # --- Operation type breakdown ---
    types = [(r.type or "").strip().lower() for r in records]
    breakdown = {k: int(v) for k, v in Counter(types).items()}

    # --- Average operand count ---
    operand_counts = [len(r.inputs) if r.inputs else 0 for r in records]
    avg_operands = float(sum(operand_counts) / total)

    # --- Most used operation ---
    most_used = max(breakdown, key=breakdown.get) if breakdown else None

    # --- Last calculation timestamp (converted to ISO8601) ---
    last_dt = max(records, key=lambda r: r.created_at).created_at

    # Convert timestamp to ISO string
    try:    
        if isinstance(last_dt, datetime):
            last_calc = last_dt.isoformat()
        else:       # pragma: no cover
            parsed = datetime.fromisoformat(str(last_dt).replace(" ", "T"))
            last_calc = parsed.isoformat()
    except Exception: # pragma: no cover
        last_calc = None

    return {
        "total_calculations": total,
        "average_operands": avg_operands,
        "operations_breakdown": breakdown,
        "most_used_operation": most_used,
        "last_calculation_date": last_calc,
    }
