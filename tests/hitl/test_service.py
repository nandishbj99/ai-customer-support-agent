from datetime import datetime, timedelta, timezone
import pytest
from app.hitl.service import ApprovalService
from app.hitl.state_machine import ApprovalState, InvalidStateTransitionError
from app.seeds.seed_data import det_uuid
from app.tools.factory import ToolServiceFactory
from app.agent.tool_router import ToolRouter


@pytest.mark.asyncio
async def test_create_and_get_approval_request(db_session):
    service = ApprovalService(db_session=db_session)
    user_id = str(det_uuid(4))  # user_004

    req = await service.create_request(
        session_id="sess_test_101",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"txn_id": str(det_uuid(204)), "amount_inr": 12000.0, "reason": "Test refund"},
        context={"reasoning": "High value flight cancellation refund"},
    )
    assert req.id is not None
    assert req.status == ApprovalState.PENDING.value
    assert req.required_role == "agent"
    assert req.priority == 3
    assert req.amount_paise == 1200000

    # Fetch request
    fetched = await service.get_request(str(req.id))
    assert fetched is not None
    assert fetched.tool_name == "initiateRefund"
    assert len(fetched.audit_logs) == 1
    assert fetched.audit_logs[0].action == "CREATED"


@pytest.mark.asyncio
async def test_list_pending_requests_prioritization(db_session):
    service = ApprovalService(db_session=db_session)
    user_id = str(det_uuid(1))

    # Low priority request
    req1 = await service.create_request(
        session_id="sess_1",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 15000.0},
    )
    # High priority executive request (amount > ₹100,000)
    req2 = await service.create_request(
        session_id="sess_2",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 150000.0},
    )

    pending = await service.list_pending_requests()
    assert len(pending) >= 2
    # req2 with priority 1 should come before req1 with priority 3
    req_ids = [str(r.id) for r in pending]
    assert req_ids.index(str(req2.id)) < req_ids.index(str(req1.id))


@pytest.mark.asyncio
async def test_approve_request_and_execute_tool(db_session):
    service = ApprovalService(db_session=db_session)
    tools = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    router = ToolRouter(services=tools)

    user_id = str(det_uuid(4))
    txn_id = str(det_uuid(204))  # ₹15,000 transaction

    req = await service.create_request(
        session_id="sess_approve_exec",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"txn_id": txn_id, "amount_inr": 11000.0, "reason": "Passenger refund"},
    )

    result = await service.approve_request(
        request_id=str(req.id),
        approver_id="agent_smith_007",
        approver_role="agent",
        tool_router=router,
        comment="Verified flight cancellation with airline records",
    )

    assert result["status"] == ApprovalState.EXECUTED.value
    assert result["execution_result"] is not None
    assert result["execution_result"]["success"] is True

    # Check database state
    updated = await service.get_request(str(req.id))
    assert updated.status == ApprovalState.EXECUTED.value
    assert updated.approver_id == "agent_smith_007"
    actions = [log.action for log in updated.audit_logs]
    assert "CREATED" in actions
    assert "APPROVED" in actions
    assert "EXECUTED" in actions


@pytest.mark.asyncio
async def test_approve_role_permission_enforcement(db_session):
    service = ApprovalService(db_session=db_session)
    user_id = str(det_uuid(1))

    # Create manager-level request (₹150,000 refund)
    req = await service.create_request(
        session_id="sess_manager_check",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 150000.0},
    )
    assert req.required_role == "manager"

    # Agent attempts to approve manager-only request -> PermissionError
    with pytest.raises(PermissionError, match="Manager authorization"):
        await service.approve_request(
            request_id=str(req.id),
            approver_id="junior_agent_1",
            approver_role="agent",
        )

    # Manager approves -> Succeeds
    res = await service.approve_request(
        request_id=str(req.id),
        approver_id="senior_manager_1",
        approver_role="manager",
    )
    assert res["status"] == ApprovalState.APPROVED.value


@pytest.mark.asyncio
async def test_reject_request_with_reason(db_session):
    service = ApprovalService(db_session=db_session)
    user_id = str(det_uuid(1))

    req = await service.create_request(
        session_id="sess_reject",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 20000.0},
    )

    # Reject without reason -> ValueError
    with pytest.raises(ValueError, match="mandatory"):
        await service.reject_request(
            request_id=str(req.id),
            approver_id="agent_1",
            approver_role="agent",
            rejection_reason="",
        )

    # Reject with valid reason
    rejected = await service.reject_request(
        request_id=str(req.id),
        approver_id="agent_1",
        approver_role="agent",
        rejection_reason="Merchant provided proof of completed service",
    )
    assert rejected["status"] == ApprovalState.REJECTED.value

    updated = await service.get_request(str(req.id))
    assert updated.status == ApprovalState.REJECTED.value
    assert updated.rejection_reason == "Merchant provided proof of completed service"


@pytest.mark.asyncio
async def test_escalate_and_auto_escalate_slas(db_session):
    service = ApprovalService(db_session=db_session)
    user_id = str(det_uuid(1))

    # Manual escalation
    req1 = await service.create_request(
        session_id="sess_esc",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 15000.0},
    )
    esc_res = await service.escalate_request(
        request_id=str(req1.id),
        actor_id="agent_1",
        actor_role="agent",
        reason="Requires legal review",
    )
    assert esc_res["status"] == ApprovalState.ESCALATED.value
    assert esc_res["required_role"] == "manager"

    # Expired SLA auto-escalation
    req2 = await service.create_request(
        session_id="sess_sla",
        user_id=user_id,
        tool_name="initiateRefund",
        tool_arguments={"amount_inr": 14000.0},
    )
    # Manually backdate sla_expires_at to simulate timeout
    req2.sla_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    await db_session.flush()

    escalated_count = await service.auto_escalate_expired_slas()
    assert escalated_count >= 1

    updated2 = await service.get_request(str(req2.id))
    assert updated2.status == ApprovalState.ESCALATED.value
    assert updated2.required_role == "manager"
