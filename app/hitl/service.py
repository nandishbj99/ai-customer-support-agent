import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.core.models import ApprovalAuditLog, ApprovalRequest, ApprovalRule, User
from app.hitl.rules_engine import ApprovalRulesEngine, RuleEvaluationResult
from app.hitl.state_machine import ApprovalState, ApprovalStateMachine, InvalidStateTransitionError
from app.tools.schemas import ToolResult

logger = structlog.get_logger()


class ApprovalNotificationManager:
    """Manages real-time WebSocket subscriber connections for HITL queues."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("hitl_websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("hitl_websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event payload to all connected dashboard clients."""
        payload = {"event": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "payload": data}
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)


# Global notification singleton
notification_manager = ApprovalNotificationManager()


class ApprovalService:
    """Core HITL service orchestrating requests, transitions, audit trails, and execution resumption."""

    def __init__(self, db_session: AsyncSession, rules_engine: Optional[ApprovalRulesEngine] = None):
        self.db = db_session
        self.rules_engine = rules_engine or ApprovalRulesEngine(db_session=db_session)

    async def create_request(
        self,
        session_id: str,
        user_id: str,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        evaluation: Optional[RuleEvaluationResult] = None,
    ) -> ApprovalRequest:
        """Create and persist a new ApprovalRequest in PENDING state."""
        ctx = dict(context or {})
        parsed_user_id = uuid.UUID(str(user_id))

        # If evaluation not passed, run rules engine
        if evaluation is None:
            user_stmt = select(User).where(User.id == parsed_user_id)
            user_res = await self.db.execute(user_stmt)
            user_obj = user_res.scalars().first()
            user_tier = user_obj.tier if user_obj else "standard"
            evaluation = await self.rules_engine.evaluate(
                tool_name=tool_name,
                arguments=tool_arguments,
                user_tier=user_tier,
                context=ctx,
            )

        request_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        new_request = ApprovalRequest(
            id=request_id,
            session_id=session_id,
            user_id=parsed_user_id,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            context=ctx,
            status=ApprovalState.PENDING.value,
            amount_paise=evaluation.amount_paise,
            required_role=evaluation.required_role,
            priority=evaluation.priority,
            sla_expires_at=evaluation.sla_expires_at,
            created_at=now,
            updated_at=now,
        )
        self.db.add(new_request)

        # Audit log for creation
        audit = ApprovalAuditLog(
            id=uuid.uuid4(),
            approval_id=request_id,
            action="CREATED",
            actor_id="system_rules_engine",
            actor_role="system",
            comment=evaluation.reason or f"Intercepted by rule '{evaluation.rule_name}'",
            created_at=now,
        )
        new_request.audit_logs.append(audit)
        await self.db.flush()

        logger.info(
            "approval_request_created",
            request_id=str(request_id),
            tool=tool_name,
            priority=evaluation.priority,
            required_role=evaluation.required_role,
        )

        # Broadcast event
        await notification_manager.broadcast("APPROVAL_CREATED", new_request.to_dict())
        return new_request

    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Fetch an approval request with user and audit log relationships."""
        req_uuid = uuid.UUID(str(request_id))
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.id == req_uuid)
            .options(selectinload(ApprovalRequest.user), selectinload(ApprovalRequest.audit_logs))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_pending_requests(
        self,
        required_role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ApprovalRequest]:
        """List requests sorted by urgency: priority ASC (1=highest), sla_expires_at ASC, amount_paise DESC."""
        stmt = (
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.user))
            .offset(offset)
            .limit(limit)
        )

        if status:
            stmt = stmt.where(ApprovalRequest.status == status.upper())
        else:
            stmt = stmt.where(ApprovalRequest.status.in_([ApprovalState.PENDING.value, ApprovalState.ESCALATED.value]))

        if required_role:
            stmt = stmt.where(ApprovalRequest.required_role == required_role)

        # Priority sort: priority asc (1 is most urgent), SLA expiry asc, amount desc
        stmt = stmt.order_by(
            ApprovalRequest.priority.asc(),
            ApprovalRequest.sla_expires_at.asc(),
            ApprovalRequest.amount_paise.desc().nulls_last(),
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def approve_request(
        self,
        request_id: str,
        approver_id: str,
        approver_role: str,
        tool_router: Optional[Any] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Approve a request and execute the underlying tool callback."""
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found.")

        # Verify role authorization: managers can approve anything; agents can only approve 'agent' role requests
        if request.required_role == "manager" and approver_role.lower() not in ("manager", "admin"):
            raise PermissionError("This request requires Manager authorization to approve.")

        # State transition PENDING/ESCALATED -> APPROVED
        sm = ApprovalStateMachine(initial_state=request.status)
        sm.transition("approve")

        now = datetime.now(timezone.utc)
        request.status = sm.state
        request.approver_id = approver_id
        request.updated_at = now

        # Add audit log for approval
        request.audit_logs.append(
            ApprovalAuditLog(
                id=uuid.uuid4(),
                approval_id=request.id,
                action="APPROVED",
                actor_id=approver_id,
                actor_role=approver_role,
                comment=comment or "Approved by operator.",
                created_at=now,
            )
        )

        execution_result_data: Optional[Dict[str, Any]] = None

        # Execute the tool via ToolRouter if provided
        if tool_router:
            try:
                # In order to allow execution without looping back into HITL, pass bypass flag or direct invocation
                tool_args = dict(request.tool_arguments or {})
                tool_result: ToolResult = await tool_router.execute(
                    tool_name=request.tool_name,
                    arguments=tool_args,
                    session_user_id=str(request.user_id),
                    session_id=request.session_id,
                    bypass_hitl=True,
                )

                if tool_result.is_success():
                    sm.transition("mark_executed")
                    request.status = sm.state
                    request.execution_result = tool_result.to_dict()
                    request.audit_logs.append(
                        ApprovalAuditLog(
                            id=uuid.uuid4(),
                            approval_id=request.id,
                            action="EXECUTED",
                            actor_id=approver_id,
                            actor_role=approver_role,
                            comment="Tool executed successfully upon approval.",
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                else:
                    sm.transition("mark_failed")
                    request.status = sm.state
                    request.execution_result = tool_result.to_dict()
                    request.audit_logs.append(
                        ApprovalAuditLog(
                            id=uuid.uuid4(),
                            approval_id=request.id,
                            action="FAILED",
                            actor_id=approver_id,
                            actor_role=approver_role,
                            comment=f"Tool execution failed: {tool_result.error.message if tool_result.error else 'Unknown error'}",
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                execution_result_data = tool_result.to_dict()
            except Exception as ex:
                sm.transition("mark_failed")
                request.status = sm.state
                err_dict = {"status": "error", "error_code": "EXECUTION_EXCEPTION", "message": str(ex)}
                request.execution_result = err_dict
                request.audit_logs.append(
                    ApprovalAuditLog(
                        id=uuid.uuid4(),
                        approval_id=request.id,
                        action="FAILED",
                        actor_id=approver_id,
                        actor_role=approver_role,
                        comment=f"Exception during tool execution: {str(ex)}",
                        created_at=datetime.now(timezone.utc),
                    )
                )
                execution_result_data = err_dict

        await self.db.flush()
        await notification_manager.broadcast("APPROVAL_RESOLVED", request.to_dict())

        return {
            "request_id": str(request.id),
            "status": request.status,
            "approver_id": approver_id,
            "execution_result": execution_result_data,
        }

    async def reject_request(
        self,
        request_id: str,
        approver_id: str,
        approver_role: str,
        rejection_reason: str,
    ) -> Dict[str, Any]:
        """Reject a request with mandatory reason code (FR-06)."""
        if not rejection_reason or not rejection_reason.strip():
            raise ValueError("Rejection reason is mandatory.")

        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found.")

        # State transition PENDING/ESCALATED -> REJECTED
        sm = ApprovalStateMachine(initial_state=request.status)
        sm.transition("reject")

        now = datetime.now(timezone.utc)
        request.status = sm.state
        request.approver_id = approver_id
        request.rejection_reason = rejection_reason.strip()
        request.updated_at = now

        request.audit_logs.append(
            ApprovalAuditLog(
                id=uuid.uuid4(),
                approval_id=request.id,
                action="REJECTED",
                actor_id=approver_id,
                actor_role=approver_role,
                comment=rejection_reason.strip(),
                created_at=now,
            )
        )
        await self.db.flush()
        await notification_manager.broadcast("APPROVAL_RESOLVED", request.to_dict())

        return {
            "request_id": str(request.id),
            "status": request.status,
            "approver_id": approver_id,
            "rejection_reason": request.rejection_reason,
        }

    async def escalate_request(
        self,
        request_id: str,
        actor_id: str,
        actor_role: str,
        reason: str,
        target_role: str = "manager",
    ) -> Dict[str, Any]:
        """Escalate a request to a manager or higher queue (FR-05)."""
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found.")

        sm = ApprovalStateMachine(initial_state=request.status)
        sm.transition("escalate")

        now = datetime.now(timezone.utc)
        request.status = sm.state
        request.required_role = target_role
        request.priority = 1  # Bump to urgent priority
        request.updated_at = now

        request.audit_logs.append(
            ApprovalAuditLog(
                id=uuid.uuid4(),
                approval_id=request.id,
                action="ESCALATED",
                actor_id=actor_id,
                actor_role=actor_role,
                comment=reason or "Escalated to senior management queue.",
                created_at=now,
            )
        )
        await self.db.flush()
        await notification_manager.broadcast("APPROVAL_ESCALATED", request.to_dict())

        return {
            "request_id": str(request.id),
            "status": request.status,
            "required_role": request.required_role,
            "priority": request.priority,
        }

    async def auto_escalate_expired_slas(self) -> int:
        """Scan for PENDING requests with expired SLAs and auto-escalate them (FR-05)."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.status == ApprovalState.PENDING.value)
            .where(ApprovalRequest.sla_expires_at < now)
        )
        res = await self.db.execute(stmt)
        expired_requests = list(res.scalars().all())

        escalated_count = 0
        for req in expired_requests:
            try:
                sm = ApprovalStateMachine(initial_state=req.status)
                sm.transition("escalate")
                req.status = sm.state
                req.required_role = "manager"
                req.priority = 1
                req.updated_at = now
                req.audit_logs.append(
                    ApprovalAuditLog(
                        id=uuid.uuid4(),
                        approval_id=req.id,
                        action="ESCALATED",
                        actor_id="system_sla_monitor",
                        actor_role="system",
                        comment="SLA expired (> 30 mins) without operator action. Auto-escalated to manager.",
                        created_at=now,
                    )
                )
                escalated_count += 1
            except Exception as e:
                logger.error("auto_escalation_error", request_id=str(req.id), error=str(e))

        if escalated_count > 0:
            await self.db.flush()
            logger.info("auto_escalated_expired_requests", count=escalated_count)

        return escalated_count
