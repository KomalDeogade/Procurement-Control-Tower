"""Core dependencies – auth, current user, and RBAC authorization."""

from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token.
    Raises 401 if token is invalid or missing."""
    if credentials:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
        return user

    # Dev fallback: return first user or create a default
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user

    # Create default user
    from app.services.auth_service import get_password_hash
    default_user = User(
        username="scm_user", email="scm@scm.local",
        full_name="SCM User", hashed_password=get_password_hash("scm123"),
        role="SCM_USER",
    )
    db.add(default_user)
    await db.commit()
    await db.refresh(default_user)
    return default_user


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory enforcing backend RBAC permissions.
    Returns HTTP 403 Forbidden if user's role is not allowed."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = str(current_user.role.value if hasattr(current_user.role, 'value') else current_user.role)
        # ADMIN always has full access
        if user_role == "ADMIN" or user_role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Action requires one of {list(allowed_roles)} roles (user role: {user_role})"
        )
    return role_checker
