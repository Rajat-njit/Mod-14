"""
Calculation Schemas Module
"""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class CalculationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"
    EXPONENTIATION = "exponentiation"
    POWER = "power"
    MODULUS = "modulus"


class CalculationBase(BaseModel):
    type: CalculationType = Field(...)
    inputs: List[float] = Field(...)

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs_is_list(cls, v):
        """
        Allow ANY list shape; length rules handled inside business logic
        to produce 400 instead of 422.
        """
        if not isinstance(v, list):
            raise ValueError("Input should be a valid list.")
        return v

    @model_validator(mode='after')
    def validate_inputs(self):
        """
        DO NOT enforce length >= 2 here.
        This belongs to operation classes to allow test expecting 400.
        """
        if self.type == CalculationType.DIVISION:
            if len(self.inputs) >= 2 and any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(from_attributes=True)


class CalculationCreate(CalculationBase):
    user_id: UUID = Field(...)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "addition",
                "inputs": [1, 2],
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class CalculationUpdate(BaseModel):
    inputs: Optional[List[float]] = None

    @model_validator(mode='after')
    def validate_inputs(self):
        # Allow empty updates
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        return self

    model_config = ConfigDict(from_attributes=True)


class CalculationResponse(CalculationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    result: float

    model_config = ConfigDict(from_attributes=True)
