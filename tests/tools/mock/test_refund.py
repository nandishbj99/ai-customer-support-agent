import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.refund import MockRefundService


@pytest.mark.asyncio
async def test_tc08_initiate_refund_above_hitl_threshold(db_session):
    """TC-08: initiateRefund with amount > ₹10,000 returns status: pending_approval and requires_hitl: True."""
    service = MockRefundService(db_session)
    # user_004 owns txn_204 with amount ₹15,000 (1,500,000 paise)
    res = await service.initiate_refund(
        txn_id=str(det_uuid(204)),
        user_id=str(det_uuid(4)),
        amount_inr=12000.0,  # ₹12,000 > ₹10,000 threshold
        reason="Flight cancelled by airline, passenger requested full refund",
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["status"] == "pending_approval"
    assert res.data["requires_hitl"] is True
    assert "exceeds ₹10,000" in res.data["message"]


@pytest.mark.asyncio
async def test_tc09_initiate_refund_under_hitl_threshold(db_session):
    """TC-09: initiateRefund with amount <= ₹10,000 returns status: processing and auto-approved."""
    service = MockRefundService(db_session)
    # user_001 owns txn_201 with amount ₹5,000
    res = await service.initiate_refund(
        txn_id=str(det_uuid(201)),
        user_id=str(det_uuid(1)),
        amount_inr=500.0,  # ₹500 <= ₹10,000
        reason="Partial discount refund for delivery delay",
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["status"] == "processing"
    assert res.data["requires_hitl"] is False
    assert res.data["amount_inr"] == 500.0


@pytest.mark.asyncio
async def test_get_refund_status_by_txn_id(db_session):
    """getRefundStatus returns existing refund details."""
    service = MockRefundService(db_session)
    # user_003 has refund_401 on txn_203 (₹1,200 completed)
    res = await service.get_refund_status(
        user_id=str(det_uuid(3)),
        txn_id=str(det_uuid(203)),
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["status"] == "completed"
    assert res.data["amount_inr"] == 1200.0


@pytest.mark.asyncio
async def test_initiate_refund_exceeds_transaction_amount(db_session):
    """Cannot refund more than the original transaction amount."""
    service = MockRefundService(db_session)
    # txn_201 is ₹5,000
    res = await service.initiate_refund(
        txn_id=str(det_uuid(201)),
        user_id=str(det_uuid(1)),
        amount_inr=7000.0,  # > ₹5,000
        reason="Invalid excess claim",
    )
    assert res.success is False
    assert res.error.code == "REFUND_EXCEEDS_TRANSACTION"


@pytest.mark.asyncio
async def test_initiate_refund_idempotent_replay(db_session):
    """Repeated call with same idempotency_key returns existing refund."""
    service = MockRefundService(db_session)
    key = "idem_test_key_999"

    # First call
    res1 = await service.initiate_refund(
        txn_id=str(det_uuid(201)),
        user_id=str(det_uuid(1)),
        amount_inr=300.0,
        reason="Duplicate order cancellation",
        idempotency_key=key,
    )
    assert res1.success is True

    # Second call with same idempotency key
    res2 = await service.initiate_refund(
        txn_id=str(det_uuid(201)),
        user_id=str(det_uuid(1)),
        amount_inr=300.0,
        reason="Duplicate order cancellation",
        idempotency_key=key,
    )
    assert res2.success is True
    assert res2.data["is_idempotent_replay"] is True
    assert res2.data["idempotency_key"] == key
