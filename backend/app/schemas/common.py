"""
backend/app/schemas/common.py — Common schema primitives and enums
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class HandRaiseClass(str, Enum):
    HAND_RAISED = "hand_raised"
    HAND_NOT_RAISED = "hand_not_raised"
    AMBIGUOUS = "ambiguous"


class DataStatus(str, Enum):
    REAL = "REAL"
    DEMO_DATA = "DEMO_DATA"
    NOT_CONNECTED = "NOT_CONNECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    READY = "READY"


class CamelModel(BaseModel):
    """Base model that populates both camelCase and snake_case."""

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )

