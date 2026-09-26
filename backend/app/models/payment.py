"""Payment model – tracks payment against invoices (mock payment service in V1)."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    WIRE = "WIRE"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # PAY-800001
    invoice_id = Column(
        Integer, ForeignKey("invoices.id"), nullable=False
    )
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True))
    payment_method = Column(
        Enum(PaymentMethod), default=PaymentMethod.BANK_TRANSFER
    )
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    reference_number = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ────────────────────────────────────
    invoice = relationship("Invoice", back_populates="payments")
