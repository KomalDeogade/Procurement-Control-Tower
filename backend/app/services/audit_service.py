"""Audit service – records every important state transition."""

import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: dict | None = None,
    new_value: dict | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """Create an immutable audit log entry."""
    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        timestamp=datetime.now(timezone.utc),
        old_value=json.dumps(old_value) if old_value else None,
        new_value=json.dumps(new_value) if new_value else None,
        metadata_=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    await db.flush()
    return entry
