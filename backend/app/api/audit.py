"""Audit Logs API – read-only access to audit trail."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas import AuditLogResponse

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if action:
        q = q.where(AuditLog.action == action)
    result = await db.execute(q)
    logs = result.scalars().all()
    return {"value": [AuditLogResponse.model_validate(l).model_dump() for l in logs], "count": len(logs)}
