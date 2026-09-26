"""Invoice model – supplier invoices matched against purchase orders."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VALIDATED = "VALIDATED"
    DISCREPANCY = "DISCREPANCY"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # INV-220001
    po_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False
    )
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False
    )
    invoice_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    sap_invoice_number = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    supplier = relationship("Supplier", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")
