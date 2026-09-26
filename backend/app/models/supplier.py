"""Supplier model – vendor master data with performance scores."""

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(20), unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    designation = Column(String(100))
    registration_number = Column(String(100))
    category = Column(String(100))
    location = Column(String(255))
    quality_score = Column(Float, default=0.0)
    delivery_score = Column(Float, default=0.0)
    historical_performance = Column(Text)  # JSON string of past metrics
    risk_score = Column(Float, default=0.0)
    payment_terms = Column(String(100))
    approval_status = Column(String(20), default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    rfqs = relationship("RFQ", back_populates="supplier")
    quotes = relationship("SupplierQuote", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    invoices = relationship("Invoice", back_populates="supplier")
