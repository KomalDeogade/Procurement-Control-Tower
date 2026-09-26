"""Supplier schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class SupplierCreate(BaseModel):
    supplier_code: str
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    registration_number: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    payment_terms: Optional[str] = None


class SupplierUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quality_score: Optional[float] = None
    delivery_score: Optional[float] = None
    risk_score: Optional[float] = None
    payment_terms: Optional[str] = None
    approval_status: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    supplier_code: str
    company_name: str
    contact_person: str | None
    email: str | None
    phone: str | None
    designation: str | None
    registration_number: str | None
    category: str | None
    location: str | None
    quality_score: float
    delivery_score: float
    risk_score: float
    payment_terms: str | None
    approval_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
