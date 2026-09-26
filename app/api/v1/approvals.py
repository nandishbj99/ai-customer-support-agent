import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tool_router import ToolRouter
from app.core.database import get_db_session
from app.hitl.service import ApprovalService, notification_manager
from app.hitl.state_machine import InvalidStateTransitionError
from app.tools.factory import ToolServiceFactory

router = APIRouter(prefix="/approvals", tags=["Human-in-the-Loop Approvals"])


# Schemas
class ApproveRequestPayload(BaseModel):
    approver_id: str = Field(..., description="ID of the human operator approving the request")
    approver_role: str = Field(default="agent", description="Role of the operator: agent, manager, admin")
    comment: Optional[str] = Field(default=None, description="Optional approval notes or comments")


class RejectRequestPayload(BaseModel):
    approver_id: str = Field(..., description="ID of the human operator rejecting the request")
    approver_role: str = Field(default="agent", description="Role of the operator: agent, manager, admin")
    rejection_reason: str = Field(..., min_length=3, description="Mandatory reason for rejection (FR-06)")


class EscalateRequestPayload(BaseModel):
    actor_id: str = Field(..., description="ID of the operator escalating the request")
    actor_role: str = Field(default="agent", description="Current operator role")
    reason: str = Field(..., min_length=3, description="Reason for escalation to higher supervisory tier")
    target_role: str = Field(default="manager", description="Target role: manager or senior_manager")


def get_approval_service(db: AsyncSession = Depends(get_db_session)) -> ApprovalService:
    return ApprovalService(db_session=db)


def get_tool_router(db: AsyncSession = Depends(get_db_session)) -> ToolRouter:
    services = ToolServiceFactory.create_services(mode="mock", db_session=db)
    return ToolRouter(services=services)


@router.websocket("/ws")
async def websocket_approval_notifications(websocket: WebSocket):
    """Real-time WebSocket stream of new approval requests and state transitions (FR-10)."""
    await notification_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients can send ping or keepalive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
    except Exception:
        notification_manager.disconnect(websocket)


@router.get("", response_model=List[Dict[str, Any]])
async def list_approval_requests(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, ESCALATED, APPROVED, etc.)"),
    role: Optional[str] = Query(None, description="Filter by required role (agent, manager)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ApprovalService = Depends(get_approval_service),
):
    """List pending and escalated approval requests sorted by priority and SLA expiry (FR-03, FR-04)."""
    requests = await service.list_pending_requests(
        required_role=role,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [r.to_dict() for r in requests]


@router.get("/{request_id}", response_model=Dict[str, Any])
async def get_approval_request(
    request_id: str,
    service: ApprovalService = Depends(get_approval_service),
):
    """Retrieve full context and audit history for an approval request (FR-01, FR-07)."""
    try:
        req = await service.get_request(request_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid request UUID format.")

    if not req:
        raise HTTPException(status_code=404, detail=f"Approval request '{request_id}' not found.")

    res = req.to_dict()
    res["audit_logs"] = [log.to_dict() for log in req.audit_logs]
    if req.user:
        res["customer_name"] = req.user.name
        res["customer_email"] = req.user.email
        res["customer_tier"] = req.user.tier
    return res


@router.post("/{request_id}/approve", response_model=Dict[str, Any])
async def approve_request(
    request_id: str,
    payload: ApproveRequestPayload,
    service: ApprovalService = Depends(get_approval_service),
    router: ToolRouter = Depends(get_tool_router),
):
    """Approve a pending request and immediately execute the underlying tool (FR-04, FR-08)."""
    try:
        result = await service.approve_request(
            request_id=request_id,
            approver_id=payload.approver_id,
            approver_role=payload.approver_role,
            tool_router=router,
            comment=payload.comment,
        )
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except InvalidStateTransitionError as ie:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ie))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{request_id}/reject", response_model=Dict[str, Any])
async def reject_request(
    request_id: str,
    payload: RejectRequestPayload,
    service: ApprovalService = Depends(get_approval_service),
):
    """Reject a pending request with a mandatory reason code (FR-06)."""
    try:
        result = await service.reject_request(
            request_id=request_id,
            approver_id=payload.approver_id,
            approver_role=payload.approver_role,
            rejection_reason=payload.rejection_reason,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except InvalidStateTransitionError as ie:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ie))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{request_id}/escalate", response_model=Dict[str, Any])
async def escalate_request(
    request_id: str,
    payload: EscalateRequestPayload,
    service: ApprovalService = Depends(get_approval_service),
):
    """Escalate a request to senior management (FR-05)."""
    try:
        result = await service.escalate_request(
            request_id=request_id,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            reason=payload.reason,
            target_role=payload.target_role,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except InvalidStateTransitionError as ie:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ie))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auto-escalate", response_model=Dict[str, Any])
async def trigger_auto_escalation(
    service: ApprovalService = Depends(get_approval_service),
):
    """Trigger background check for requests with expired SLAs and auto-escalate them (FR-05)."""
    count = await service.auto_escalate_expired_slas()
    return {"status": "success", "escalated_count": count}
