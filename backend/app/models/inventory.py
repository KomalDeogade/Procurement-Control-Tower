"""Inventory models – current stock levels, risk, and transaction history."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class TransactionType(str, enum.Enum):
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
    TRANSFER = "TRANSFER"


class StockRiskStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"
    STOCKOUT_RISK = "STOCKOUT_RISK"


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), unique=True, nullable=False, index=True)
    material_name = Column(String(255), nullable=False)
    quantity_on_hand = Column(Float, default=0.0)
    unit = Column(String(20), nullable=False)
    plant = Column(String(50))
    warehouse = Column(String(50))
    reorder_level = Column(Float, default=0.0)
    safety_stock = Column(Float, default=0.0)
    minimum_stock = Column(Float, default=0.0)
    average_daily_consumption = Column(Float, default=0.0)
    lead_time_days = Column(Integer, default=7)
    reserved_quantity = Column(Float, default=0.0)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    transactions = relationship(
        "InventoryTransaction", back_populates="inventory_item"
    )


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(
        Integer, ForeignKey("inventory_items.id"), nullable=False
    )
    transaction_type = Column(
        Enum(TransactionType), nullable=False
    )
    quantity = Column(Float, nullable=False)
    reference_type = Column(String(50))  # e.g. "goods_receipt", "purchase_order"
    reference_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # ── Relationships ────────────────────────────────────
    inventory_item = relationship(
        "InventoryItem", back_populates="transactions"
    )
