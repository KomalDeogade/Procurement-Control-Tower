"""PurchaseOrder model – created after requirement approval, synced with SAP."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class POStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_SAP = "PENDING_SAP"
    SAP_CREATED = "SAP_CREATED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    INVOICED = "INVOICED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # PO-450001
    requirement_id = Column(
        Integer, ForeignKey("requirements.id"), nullable=False
    )
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False
    )
    quote_id = Column(Integer, ForeignKey("supplier_quotes.id"))
    sap_po_number = Column(String(50))           # PO number from (Mock) SAP
    material_code = Column(String(50), nullable=False)
    material_name = Column(String(255))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    delivery_date = Column(DateTime)
    status = Column(Enum(POStatus), default=POStatus.DRAFT)
    payment_terms = Column(String(100))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    requirement = relationship("Requirement", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")
    invoices = relationship("Invoice", back_populates="purchase_order")
