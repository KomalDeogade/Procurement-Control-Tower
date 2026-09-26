"""GoodsReceipt model – records materials received against a purchase order."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class GRNStatus(str, enum.Enum):
    PENDING_INSPECTION = "PENDING_INSPECTION"
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # GRN-500001
    po_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False
    )
    received_quantity = Column(Float, nullable=False)
    received_date = Column(DateTime(timezone=True), server_default=func.now())
    quality_status = Column(
        Enum(GRNStatus), default=GRNStatus.PENDING_INSPECTION
    )
    inspector = Column(String(255))
    remarks = Column(Text)
    sap_grn_number = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ────────────────────────────────────
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
