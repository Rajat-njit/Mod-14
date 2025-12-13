import uuid
import pytest

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
    Exponentiation,
    Power,
    Modulus,
)


def test_factory_creates_addition():
    calc = Calculation.create("addition", uuid.uuid4(), [1, 2])
    assert isinstance(calc, Addition)


def test_factory_creates_subtraction():
    calc = Calculation.create("subtraction", uuid.uuid4(), [5, 3])
    assert isinstance(calc, Subtraction)


def test_factory_creates_multiplication():
    calc = Calculation.create("multiplication", uuid.uuid4(), [2, 3])
    assert isinstance(calc, Multiplication)


def test_factory_creates_division():
    calc = Calculation.create("division", uuid.uuid4(), [10, 2])
    assert isinstance(calc, Division)


def test_factory_creates_exponentiation():
    calc = Calculation.create("exponentiation", uuid.uuid4(), [2, 3])
    assert isinstance(calc, Exponentiation)


def test_factory_creates_power_alias():
    calc = Calculation.create("power", uuid.uuid4(), [2, 4])
    assert isinstance(calc, Power)


def test_factory_creates_modulus():
    calc = Calculation.create("modulus", uuid.uuid4(), [10, 3])
    assert isinstance(calc, Modulus)


def test_factory_strips_and_lowercases():
    calc = Calculation.create("  Addition  ", uuid.uuid4(), [1, 2])
    assert isinstance(calc, Addition)


def test_factory_rejects_unknown_type():
    with pytest.raises(ValueError):
        Calculation.create("unknown", uuid.uuid4(), [1, 2])


def test_factory_rejects_non_string_type():
    with pytest.raises(ValueError):
        Calculation.create(123, uuid.uuid4(), [1, 2])
