"""SupplierQuote model – quotation submitted by a supplier for a requirement."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class QuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SupplierQuote(Base):
    __tablename__ = "supplier_quotes"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # QUOTE-1001
    requirement_id = Column(
        Integer, ForeignKey("requirements.id"), nullable=False
    )
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False
    )
    unit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    freight = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    availability = Column(String(50))
    lead_time_days = Column(Integer)
    delivery_date = Column(DateTime)
    payment_terms = Column(String(100))
    warranty = Column(String(255))
    service_details = Column(Text)
    advantages = Column(Text)
    limitations = Column(Text)
    quotation_document = Column(String(500))  # file path / URL
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    requirement = relationship("Requirement", back_populates="quotes")
    supplier = relationship("Supplier", back_populates="quotes")
