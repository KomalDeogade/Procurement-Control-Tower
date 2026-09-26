"""Requirement model – the starting entity of the procurement lifecycle."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class RequirementStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    RFQ_IN_PROGRESS = "RFQ_IN_PROGRESS"
    QUOTES_RECEIVED = "QUOTES_RECEIVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PO_CREATED = "PO_CREATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RequirementPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # REQ-1001
    material_code = Column(String(50), nullable=False)
    material_name = Column(String(255), nullable=False)
    description = Column(Text)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    plant = Column(String(50))
    required_by_date = Column(DateTime)
    budget = Column(Float)
    currency = Column(String(3), default="USD")
    priority = Column(
        Enum(RequirementPriority), default=RequirementPriority.MEDIUM
    )
    status = Column(
        Enum(RequirementStatus), default=RequirementStatus.DRAFT
    )
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    creator = relationship("User", back_populates="requirements")
    rfqs = relationship("RFQ", back_populates="requirement")
    quotes = relationship("SupplierQuote", back_populates="requirement")
    purchase_orders = relationship("PurchaseOrder", back_populates="requirement")

