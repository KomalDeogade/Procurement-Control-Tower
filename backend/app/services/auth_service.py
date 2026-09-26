"""
Authentication service – login, registration, token management.

Designed as a thin layer so Keycloak can replace it later.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.models.user import User, UserRole


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """Validate credentials and return user or None."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def create_user(db: AsyncSession, username: str, email: str,
                      full_name: str, password: str, role: str = "SCM_USER") -> User:
    """Register a new user."""
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=UserRole(role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def build_token(user: User) -> str:
    """Build a JWT for the given user."""
    return create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )


def verify_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    return decode_access_token(token)


async def seed_default_users(db: AsyncSession) -> None:
    """Create default prototype users if they don't already exist."""
    defaults = [
        ("admin", "admin@scm.local", "System Administrator", "admin123", "ADMIN"),
        ("scm_user", "scm@scm.local", "Rajesh Kumar", "scm123", "SCM_USER"),
        ("proc_manager", "manager@scm.local", "Anita Sharma", "manager123", "PROCUREMENT_MANAGER"),
        ("finance_user", "finance@scm.local", "Vikram Patel", "finance123", "FINANCE_USER"),
    ]
    for username, email, full_name, password, role in defaults:
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none() is None:
            user = User(
                username=username, email=email, full_name=full_name,
                hashed_password=get_password_hash(password),
                role=UserRole(role),
            )
            db.add(user)
    await db.commit()
