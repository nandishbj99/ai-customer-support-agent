import pytest
from app.agent.tool_router import ToolRouter
from app.seeds.seed_data import det_uuid
from app.tools.factory import ToolServiceFactory


@pytest.fixture
def tool_router(db_session):
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    return ToolRouter(services)


@pytest.mark.asyncio
async def test_tc17_router_dispatches_valid_tool(tool_router):
    """TC-17: ToolRouter dispatches getTransaction to correct service method."""
    user_id = str(det_uuid(1))
    txn_id = str(det_uuid(201))

    res = await tool_router.execute(
        tool_name="getTransaction",
        arguments={"txn_id": txn_id},
        session_user_id=user_id,
    )
    assert res.success is True
    assert res.data["id"] == txn_id
    assert res.data["amount_inr"] == 5000.0


@pytest.mark.asyncio
async def test_tc18_router_handles_unknown_tool(tool_router):
    """TC-18: ToolRouter returns UNKNOWN_TOOL error for non-existent tool name."""
    res = await tool_router.execute(
        tool_name="transferAllMoneyToHacker",
        arguments={},
        session_user_id=str(det_uuid(1)),
    )
    assert res.success is False
    assert res.error.code == "UNKNOWN_TOOL"


@pytest.mark.asyncio
async def test_tc22_end_to_end_router_factory_db(tool_router):
    """TC-22: Full round-trip: ToolRouter -> Factory Services -> Mock Service -> DB -> ToolResult."""
    # S-01 balance query
    res = await tool_router.execute(
        tool_name="getAccountBalance",
        arguments={},
        session_user_id=str(det_uuid(1)),
    )
    assert res.success is True
    assert res.data["balance_inr"] == 3200.0
    assert res.data["balance_paise"] == 320000


@pytest.mark.asyncio
async def test_router_session_user_id_tamper_protection(tool_router):
    """Router overrides any user_id injected by LLM with verified session_user_id."""
    # Attacker tries to query user_002's transaction (txn_202) while authenticated as user_001
    res = await tool_router.execute(
        tool_name="getTransaction",
        arguments={"txn_id": str(det_uuid(202)), "user_id": str(det_uuid(2))},  # Spoofed user_id
        session_user_id=str(det_uuid(1)),  # Real authenticated session user
    )
    # The router overwrote arguments["user_id"] to user_001, so mock service will reject as UNAUTHORIZED_ACCESS!
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_router_idempotency_key_auto_generation(tool_router):
    """Router automatically computes idempotency key for initiateRefund when omitted."""
    user_id = str(det_uuid(1))
    txn_id = str(det_uuid(201))

    res = await tool_router.execute(
        tool_name="initiateRefund",
        arguments={
            "txn_id": txn_id,
            "amount_inr": 250.0,
            "reason": "Late delivery partial refund",
        },
        session_user_id=user_id,
        session_id="session_xyz_789",
    )
    assert res.success is True
    assert res.data["amount_inr"] == 250.0
    assert res.data["status"] == "processing"


@pytest.mark.asyncio
async def test_router_search_policy_delegation(tool_router):
    """Router executes searchPolicy and returns policy guidance."""
    res = await tool_router.execute(
        tool_name="searchPolicy",
        arguments={"query": "refund timeline for failed UPI"},
        session_user_id=str(det_uuid(1)),
    )
    assert res.success is True
    assert len(res.data["results"]) > 0
