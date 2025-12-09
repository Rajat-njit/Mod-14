from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class CalculationStats(BaseModel):
    """
    Aggregated usage statistics for a user's calculations.
    """

    total_calculations: int = Field(..., ge=0)
    average_operands: float = Field(..., ge=0)
    operations_breakdown: Dict[str, int]
    most_used_operation: Optional[str] = None

    # Force safe string output for date
    last_calculation_date: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_calculations": 7,
                "average_operands": 2.57,
                "operations_breakdown": {
                    "addition": 3,
                    "subtraction": 2,
                    "multiplication": 1,
                    "division": 1,
                },
                "most_used_operation": "addition",
                "last_calculation_date": "2025-12-05T02:18:00"
            }
        }
    )
