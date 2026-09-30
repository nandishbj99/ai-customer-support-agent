from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.security.audit import AuditService
from app.security.dependencies import requires_role
from app.security.roles import UserRole

router = APIRouter(prefix="/audit", tags=["Security & Compliance Audit Logs"])


def get_audit_service(db: AsyncSession = Depends(get_db_session)) -> AuditService:
    return AuditService(db_session=db)


@router.get(
    "/logs",
    response_model=List[Dict[str, Any]],
    dependencies=[Depends(requires_role([UserRole.SUPERVISOR, UserRole.ADMIN]))],
)
async def list_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, FAILURE, BLOCKED)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AuditService = Depends(get_audit_service),
) -> List[Dict[str, Any]]:
    """Retrieve audit logs with RBAC restriction (SUPERVISOR and ADMIN only) (FR-03, FR-06)."""
    logs = await service.query_logs(
        event_type=event_type,
        actor_id=actor_id,
        session_id=session_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [log.to_dict() for log in logs]
