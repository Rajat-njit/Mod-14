"""
Calculation Models Module
"""

from datetime import datetime
import uuid
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base


class AbstractCalculation:
    @declared_attr
    def __tablename__(cls):
        return "calculations"

    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )

    @declared_attr
    def type(cls):
        return Column(String(50), nullable=False, index=True)

    @declared_attr
    def inputs(cls):
        return Column(JSON, nullable=False)

    @declared_attr
    def result(cls):
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Calculation(Base, AbstractCalculation):

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }

    user = relationship("User", back_populates="calculations")

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


    @staticmethod
    def create(calculation_type: str, user_id, inputs):
        print("FACTORY LOADED FROM:", __file__)
        print("FACTORY TYPE RECEIVED:", calculation_type, type(calculation_type))

        # Strict check
        if not isinstance(calculation_type, str):
            print("RAISING: not a string")
            raise ValueError("Unsupported calculation type")

        calc_key = calculation_type.strip().lower()
        print("NORMALIZED TYPE:", calc_key)

        mapping = {
            "addition": Addition,
            "subtraction": Subtraction,
            "multiplication": Multiplication,
            "division": Division,
            "exponentiation": Exponentiation,
            "power": Power,
            "modulus": Modulus,
        }

        cls = mapping.get(calc_key)
        print("MAPPING RESULT:", cls)

        if cls is None:
            print("RAISING: mapping returned None")
            raise ValueError("Unsupported calculation type")

        return cls(user_id=user_id, inputs=inputs)





# Subclasses -------------------------------------------------------------

class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        return sum(self.inputs)


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for v in self.inputs[1:]:
            result -= v
        return result


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = 1
        for v in self.inputs:
            result *= v
        return result


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for v in self.inputs[1:]:
            if v == 0:
                raise ValueError("Cannot divide by zero.")
            result /= v
        return result


class Exponentiation(Calculation):
    __mapper_args__ = {"polymorphic_identity": "exponentiation"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for v in self.inputs[1:]:
            result = result ** v
        return float(result)


class Power(Calculation):
    __mapper_args__ = {"polymorphic_identity": "power"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) != 2:
            raise ValueError("Power requires exactly 2 values.")
        return float(self.inputs[0] ** self.inputs[1])


class Modulus(Calculation):
    __mapper_args__ = {"polymorphic_identity": "modulus"}

    def get_result(self):
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) != 2:
            raise ValueError("Modulus operation requires exactly two numbers")
        if self.inputs[1] == 0:
            raise ValueError("Modulus by zero undefined.")
        return float(self.inputs[0] % self.inputs[1])
