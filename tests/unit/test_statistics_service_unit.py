import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.statistics_service import compute_user_stats


# ---- FAKE MODEL ----
class FakeCalculation:
    def __init__(self, user_id, type, inputs, created_at):
        self.user_id = user_id
        self.type = type
        self.inputs = inputs
        self.created_at = created_at


# ---- FAKE DB SESSION ----
class FakeDB:
    def __init__(self, records):
        self._records = records

    def query(self, model):
        class _Q:
            def __init__(self, outer):
                self.outer = outer

            def filter(self, condition):
                # ignore condition (simple mock)
                return self

            def all(self):
                return self.outer._records

        return _Q(self)


# -------------------------
# BEGIN UNIT TESTS
# -------------------------
def test_stats_invalid_uuid():
    stats = compute_user_stats(FakeDB([]), "not-a-uuid")
    assert stats["total_calculations"] == 0
    assert stats["average_operands"] == 0.0


def test_stats_empty():
    stats = compute_user_stats(FakeDB([]), uuid4())
    assert stats["total_calculations"] == 0
    assert stats["operations_breakdown"] == {}


def test_stats_basic_aggregation():
    uid = uuid4()
    now = datetime.utcnow()

    records = [
        FakeCalculation(uid, "addition", [1, 2], now),
        FakeCalculation(uid, "addition", [5], now + timedelta(seconds=5)),
        FakeCalculation(uid, "multiplication", [2, 3, 4], now + timedelta(seconds=10)),
    ]

    db = FakeDB(records)
    stats = compute_user_stats(db, uid)

    assert stats["total_calculations"] == 3
    assert stats["operations_breakdown"] == {"addition": 2, "multiplication": 1}
    assert stats["most_used_operation"] == "addition"
    assert stats["average_operands"] == pytest.approx((2 + 1 + 3) / 3, rel=1e-3)
    assert stats["last_calculation_date"].startswith(str((now + timedelta(seconds=10)).date()))


def test_stats_with_missing_inputs_field():
    uid = uuid4()
    now = datetime.utcnow()

    records = [
        FakeCalculation(uid, "addition", None, now),
        FakeCalculation(uid, "addition", [], now),
    ]

    db = FakeDB(records)
    stats = compute_user_stats(db, uid)

    assert stats["average_operands"] == 0.0
    assert stats["total_calculations"] == 2
