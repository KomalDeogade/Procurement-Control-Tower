"""AuditLog model – immutable record of every state-changing operation."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(255), nullable=False)         # username or system
    action = Column(String(100), nullable=False)        # e.g. "CREATE", "UPDATE", "APPROVE"
    entity_type = Column(String(50), nullable=False)    # e.g. "requirement", "purchase_order"
    entity_id = Column(String(50), nullable=False)      # display_id or pk
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    old_value = Column(Text)                            # JSON string
    new_value = Column(Text)                            # JSON string
    metadata_ = Column("metadata", Text)                # JSON string
