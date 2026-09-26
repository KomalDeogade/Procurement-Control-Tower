"""Approval model – polymorphic approval workflow for any entity."""

import enum

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.sql import func

from app.database.session import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String(20), unique=True, index=True)
    entity_type = Column(String(50), nullable=False)   # e.g. "requirement", "purchase_order", "invoice"
    entity_id = Column(Integer, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approval_level = Column(Integer, default=1)
    status = Column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING
    )
    comments = Column(Text)
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
