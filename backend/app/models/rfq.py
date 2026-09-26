"""RFQ model – Request for Quotation sent to suppliers."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class RFQStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    RESPONDED = "RESPONDED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)  # RFQ-3001
    requirement_id = Column(
        Integer, ForeignKey("requirements.id"), nullable=False
    )
    supplier_id = Column(
        Integer, ForeignKey("suppliers.id"), nullable=False
    )
    status = Column(Enum(RFQStatus), default=RFQStatus.DRAFT)
    access_token = Column(String(100), unique=True, index=True, nullable=True)  # Secure tokenized link
    response_deadline = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    requirement = relationship("Requirement", back_populates="rfqs")
    supplier = relationship("Supplier", back_populates="rfqs")
