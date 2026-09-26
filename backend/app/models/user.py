"""User model – authentication and role management."""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class UserRole(str, enum.Enum):
    SUPPLIER = "SUPPLIER"
    SCM_USER = "SCM_USER"
    PROCUREMENT_MANAGER = "PROCUREMENT_MANAGER"
    STORE_USER = "STORE_USER"
    FINANCE_USER = "FINANCE_USER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.SCM_USER, nullable=False)
    supplier_id = Column(Integer, nullable=True)  # Linked supplier ID if role == SUPPLIER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────
    requirements = relationship("Requirement", back_populates="creator")
    notifications = relationship("Notification", back_populates="user")
