# tests/unit/test_calculation_schema_unit.py

import uuid
import pytest
from datetime import datetime

from app.schemas.calculation import (
    CalculationBase,
    CalculationCreate,
    CalculationUpdate,
    CalculationResponse,
    CalculationType,
)


# ---------------------------
# TYPE VALIDATION
# ---------------------------

def test_invalid_calculation_type():
    with pytest.raises(ValueError, match="Type must be one of"):
        CalculationBase(type="invalid", inputs=[1, 2])


def test_valid_calculation_type_case_insensitive():
    schema = CalculationBase(type="ADDITION", inputs=[1, 2])
    assert schema.type == CalculationType.ADDITION


# ---------------------------
# INPUT VALIDATION
# ---------------------------

def test_inputs_must_be_list():
    with pytest.raises(ValueError, match="Input should be a valid list"):
        CalculationBase(type="addition", inputs="not-a-list")


def test_division_by_zero_validator():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        CalculationBase(type="division", inputs=[10, 0])


def test_division_valid_inputs():
    schema = CalculationBase(type="division", inputs=[10, 2])
    assert schema.inputs == [10, 2]


# ---------------------------
# CREATE SCHEMA
# ---------------------------

def test_calculation_create_valid():
    schema = CalculationCreate(
        type="addition",
        inputs=[1, 2],
        user_id=uuid.uuid4()
    )

    assert schema.type == CalculationType.ADDITION
    assert schema.inputs == [1, 2]


# ---------------------------
# UPDATE SCHEMA
# ---------------------------

def test_calculation_update_allows_empty():
    schema = CalculationUpdate()
    assert schema.inputs is None


def test_calculation_update_requires_two_inputs():
    with pytest.raises(ValueError, match="At least two numbers"):
        CalculationUpdate(inputs=[1])


def test_calculation_update_valid():
    schema = CalculationUpdate(inputs=[1, 2])
    assert schema.inputs == [1, 2]


# ---------------------------
# RESPONSE SCHEMA
# ---------------------------

def test_calculation_response_valid():
    now = datetime.utcnow()

    schema = CalculationResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        type="addition",
        inputs=[1, 2],
        result=3.0,
        created_at=now,
        updated_at=now,
    )

    assert schema.result == 3.0
