import uuid
import pytest

from app.models.calculation import (
    Addition,
    Subtraction,
    Multiplication,
    Division,
    Exponentiation,
    Power,
    Modulus,
)


# ------------------ ADDITION ------------------

def test_addition_happy_path():
    calc = Addition(user_id=uuid.uuid4(), inputs=[1, 2, 3])
    assert calc.get_result() == 6


def test_addition_invalid_inputs():
    calc = Addition(user_id=uuid.uuid4(), inputs="bad")
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ SUBTRACTION ------------------

def test_subtraction_happy_path():
    calc = Subtraction(user_id=uuid.uuid4(), inputs=[10, 3, 2])
    assert calc.get_result() == 5


def test_subtraction_too_few_inputs():
    calc = Subtraction(user_id=uuid.uuid4(), inputs=[5])
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ MULTIPLICATION ------------------

def test_multiplication_happy_path():
    calc = Multiplication(user_id=uuid.uuid4(), inputs=[2, 3, 4])
    assert calc.get_result() == 24


def test_multiplication_invalid_inputs():
    calc = Multiplication(user_id=uuid.uuid4(), inputs=None)
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ DIVISION ------------------

def test_division_happy_path():
    calc = Division(user_id=uuid.uuid4(), inputs=[20, 2, 2])
    assert calc.get_result() == 5


def test_division_by_zero():
    calc = Division(user_id=uuid.uuid4(), inputs=[10, 0])
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ EXPONENTIATION ------------------

def test_exponentiation_happy_path():
    calc = Exponentiation(user_id=uuid.uuid4(), inputs=[2, 3])
    assert calc.get_result() == 8.0


def test_exponentiation_invalid_inputs():
    calc = Exponentiation(user_id=uuid.uuid4(), inputs="bad")
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ POWER ------------------

def test_power_happy_path():
    calc = Power(user_id=uuid.uuid4(), inputs=[2, 4])
    assert calc.get_result() == 16.0


def test_power_requires_exact_two_inputs():
    calc = Power(user_id=uuid.uuid4(), inputs=[2, 3, 4])
    with pytest.raises(ValueError):
        calc.get_result()


# ------------------ MODULUS ------------------

def test_modulus_happy_path():
    calc = Modulus(user_id=uuid.uuid4(), inputs=[10, 3])
    assert calc.get_result() == 1.0


def test_modulus_by_zero():
    calc = Modulus(user_id=uuid.uuid4(), inputs=[10, 0])
    with pytest.raises(ValueError):
        calc.get_result()
