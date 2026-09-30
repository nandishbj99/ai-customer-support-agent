import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.models import AuditLog
from app.security.pii import redact_pii

logger = structlog.get_logger()


class AuditService:
    """Asynchronous audit logging service persisting security and system events with automatic PII scrubbing."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log_event(
        self,
        event_type: str,
        action: str,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create and persist a sanitized, structured audit log entry."""
        clean_details = redact_pii(dict(details or {}))

        log_entry = AuditLog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_address,
            session_id=session_id,
            resource=resource,
            action=action,
            status=status,
            details=clean_details,
        )
        self.db.add(log_entry)
        await self.db.flush()

        logger.info(
            "audit_event_logged",
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            status=status,
        )
        return log_entry

    async def query_logs(
        self,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Query audit log history with filtering and pagination."""
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)

        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if session_id:
            stmt = stmt.where(AuditLog.session_id == session_id)
        if status:
            stmt = stmt.where(AuditLog.status == status.upper())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
