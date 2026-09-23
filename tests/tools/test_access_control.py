import pytest
from app.agent.tool_router import ToolRouter
from app.seeds.seed_data import det_uuid
from app.tools.factory import ToolServiceFactory
from app.tools.mock.fraud import MockFraudService
from app.tools.mock.payment import MockPaymentService
from app.tools.mock.refund import MockRefundService
from app.tools.mock.transaction import MockTransactionService


@pytest.mark.asyncio
async def test_access_control_transaction_service(db_session):
    """User A cannot read User B's transaction."""
    service = MockTransactionService(db_session)
    user_a = str(det_uuid(1))
    user_b = str(det_uuid(2))
    txn_b = str(det_uuid(202))  # Belongs to user_b

    res = await service.get_transaction(txn_id=txn_b, user_id=user_a)
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_access_control_payment_service(db_session):
    """User A cannot read User B's payment."""
    service = MockPaymentService(db_session)
    user_a = str(det_uuid(1))
    user_b = str(det_uuid(2))
    txn_b = str(det_uuid(202))  # Belongs to user_b

    res = await service.get_payment_status(user_id=user_a, txn_id=txn_b)
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_access_control_fraud_service(db_session):
    """User A cannot inspect fraud risk on User B's transaction."""
    service = MockFraudService(db_session)
    user_a = str(det_uuid(1))
    txn_b = str(det_uuid(202))

    res = await service.check_fraud_status(txn_id=txn_b, user_id=user_a)
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_access_control_refund_service(db_session):
    """User A cannot read or initiate refund on User B's transaction."""
    service = MockRefundService(db_session)
    user_a = str(det_uuid(1))
    user_b = str(det_uuid(3))
    txn_b = str(det_uuid(203))  # Belongs to user_b

    # Reading refund
    res_read = await service.get_refund_status(user_id=user_a, txn_id=txn_b)
    assert res_read.success is False
    assert res_read.error.code == "UNAUTHORIZED_ACCESS"

    # Initiating refund
    res_init = await service.initiate_refund(
        txn_id=txn_b,
        user_id=user_a,
        amount_inr=100.0,
        reason="Malicious refund attempt",
    )
    assert res_init.success is False
    assert res_init.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_access_control_tool_router_session_override(db_session):
    """ToolRouter strips any attempted user_id spoofing and injects session user_id."""
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)
    router = ToolRouter(services)

    user_a = str(det_uuid(1))
    user_b = str(det_uuid(2))
    txn_b = str(det_uuid(202))

    # User A tries to pass User B's user_id in tool arguments:
    res = await router.execute(
        tool_name="getTransaction",
        arguments={"txn_id": txn_b, "user_id": user_b},
        session_user_id=user_a,
    )
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"
