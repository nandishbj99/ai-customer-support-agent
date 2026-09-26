import pytest
from app.agent.tool_router import ToolRouter
from app.hitl.rules_engine import ApprovalRulesEngine
from app.hitl.service import ApprovalService
from app.seeds.seed_data import det_uuid
from app.tools.factory import ToolServiceFactory


@pytest.mark.asyncio
async def test_tool_router_intercepts_high_value_refund(db_session):
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    approval_svc = ApprovalService(db_session=db_session)
    router = ToolRouter(services=services, approval_service=approval_svc)

    user_id = str(det_uuid(4))
    txn_id = str(det_uuid(204))

    # Invoke refund of ₹12,000 (> ₹10,000 threshold)
    result = await router.execute(
        tool_name="initiateRefund",
        arguments={
            "txn_id": txn_id,
            "amount_inr": 12000.0,
            "reason": "Flight cancellation claim",
        },
        session_user_id=user_id,
        session_id="sess_hitl_router_1",
    )

    assert result.success is True
    assert result.data["requires_hitl"] is True
    assert result.data["status"] == "pending_approval"
    assert result.data["approval_id"] is not None

    # Check request persisted in approval service
    req = await approval_svc.get_request(result.data["approval_id"])
    assert req is not None
    assert req.status == "PENDING"
    assert req.amount_paise == 1200000


@pytest.mark.asyncio
async def test_tool_router_allows_low_value_refund_without_hitl(db_session):
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    approval_svc = ApprovalService(db_session=db_session)
    router = ToolRouter(services=services, approval_service=approval_svc)

    user_id = str(det_uuid(1))
    txn_id = str(det_uuid(201))

    # Invoke refund of ₹200 (<= ₹10,000 threshold)
    result = await router.execute(
        tool_name="initiateRefund",
        arguments={
            "txn_id": txn_id,
            "amount_inr": 200.0,
            "reason": "Late delivery partial refund",
        },
        session_user_id=user_id,
        session_id="sess_hitl_router_2",
    )

    assert result.success is True
    assert result.data["requires_hitl"] is False
    assert result.data["status"] == "processing"


@pytest.mark.asyncio
async def test_tool_router_bypass_hitl_flag(db_session):
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    approval_svc = ApprovalService(db_session=db_session)
    router = ToolRouter(services=services, approval_service=approval_svc)

    user_id = str(det_uuid(4))
    txn_id = str(det_uuid(204))

    # Calling with bypass_hitl=True (e.g. during operator-approved execution)
    result = await router.execute(
        tool_name="initiateRefund",
        arguments={
            "txn_id": txn_id,
            "amount_inr": 12000.0,
            "reason": "Flight cancellation claim approved by supervisor",
        },
        session_user_id=user_id,
        session_id="sess_hitl_router_3",
        bypass_hitl=True,
    )

    # In mock mode, the service returns success
    assert result.success is True
