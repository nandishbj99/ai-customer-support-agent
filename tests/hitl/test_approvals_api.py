import httpx
import pytest
from app.core.database import get_db_session
from app.hitl.service import ApprovalService
from app.main import app
from app.seeds.seed_data import det_uuid


@pytest.mark.asyncio
async def test_approvals_api_crud_and_lifecycle(db_session):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    try:
        service = ApprovalService(db_session=db_session)
        user_id = str(det_uuid(4))
        txn_id = str(det_uuid(204))

        # Create sample request
        req = await service.create_request(
            session_id="sess_api_hitl_1",
            user_id=user_id,
            tool_name="initiateRefund",
            tool_arguments={"txn_id": txn_id, "amount_inr": 11500.0, "reason": "Test API refund"},
            context={"customer_notes": "VIP claim"},
        )
        req_id = str(req.id)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. List pending approvals
            list_res = await client.get("/api/v1/approvals")
            assert list_res.status_code == 200
            data = list_res.json()
            assert any(item["id"] == req_id for item in data)

            # 2. Get specific approval request detail
            detail_res = await client.get(f"/api/v1/approvals/{req_id}")
            assert detail_res.status_code == 200
            detail = detail_res.json()
            assert detail["id"] == req_id
            assert detail["tool_name"] == "initiateRefund"
            assert detail["status"] == "PENDING"
            assert len(detail["audit_logs"]) >= 1

            # 3. Escalate request
            esc_res = await client.post(
                f"/api/v1/approvals/{req_id}/escalate",
                json={
                    "actor_id": "agent_001",
                    "actor_role": "agent",
                    "reason": "Requires manager double check",
                    "target_role": "manager",
                },
            )
            assert esc_res.status_code == 200
            assert esc_res.json()["status"] == "ESCALATED"
            assert esc_res.json()["required_role"] == "manager"

            # 4. Agent attempts to approve manager-tier request -> 403 Forbidden
            agent_approve = await client.post(
                f"/api/v1/approvals/{req_id}/approve",
                json={
                    "approver_id": "junior_agent",
                    "approver_role": "agent",
                },
            )
            assert agent_approve.status_code == 403

            # 5. Manager approves request -> Executed successfully
            mgr_approve = await client.post(
                f"/api/v1/approvals/{req_id}/approve",
                json={
                    "approver_id": "manager_alice",
                    "approver_role": "manager",
                    "comment": "Approved after reviewing merchant log",
                },
            )
            assert mgr_approve.status_code == 200
            assert mgr_approve.json()["status"] == "EXECUTED"

            # 6. Verify detail reflects execution
            detail_after = (await client.get(f"/api/v1/approvals/{req_id}")).json()
            assert detail_after["status"] == "EXECUTED"
            assert detail_after["approver_id"] == "manager_alice"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rejection_api_validation(db_session):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    try:
        service = ApprovalService(db_session=db_session)
        user_id = str(det_uuid(1))

        req = await service.create_request(
            session_id="sess_reject_api",
            user_id=user_id,
            tool_name="initiateRefund",
            tool_arguments={"amount_inr": 15000.0},
        )
        req_id = str(req.id)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Rejection with valid reason
            rej_res = await client.post(
                f"/api/v1/approvals/{req_id}/reject",
                json={
                    "approver_id": "agent_bob",
                    "approver_role": "agent",
                    "rejection_reason": "Suspected duplicate chargeback attempt",
                },
            )
            assert rej_res.status_code == 200
            assert rej_res.json()["status"] == "REJECTED"

            # Check that approving already rejected request fails with 409 Conflict
            appr_res = await client.post(
                f"/api/v1/approvals/{req_id}/approve",
                json={"approver_id": "agent_bob", "approver_role": "agent"},
            )
            assert appr_res.status_code == 409

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auto_escalate_api_endpoint(db_session):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/v1/approvals/auto-escalate")
            assert res.status_code == 200
            assert "escalated_count" in res.json()
    finally:
        app.dependency_overrides.clear()
