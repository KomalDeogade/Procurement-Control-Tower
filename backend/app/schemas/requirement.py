"""Requirement schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RequirementCreate(BaseModel):
    material_code: str
    material_name: str
    description: Optional[str] = None
    quantity: float
    unit: str
    plant: Optional[str] = None
    required_by_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: str = "USD"
    priority: str = "MEDIUM"


class RequirementUpdate(BaseModel):
    material_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    plant: Optional[str] = None
    required_by_date: Optional[datetime] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class RequirementResponse(BaseModel):
    id: int
    display_id: str | None
    material_code: str
    material_name: str
    description: str | None
    quantity: float
    unit: str
    plant: str | None
    required_by_date: datetime | None
    budget: float | None
    currency: str
    priority: str
    status: str
    created_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
