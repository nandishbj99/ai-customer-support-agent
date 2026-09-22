import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.payment import MockPaymentService


@pytest.mark.asyncio
async def test_get_payment_status_by_txn_id(db_session):
    """Query payment status by txn_id."""
    service = MockPaymentService(db_session)
    # user_001 owns txn_201 which has payment_301
    res = await service.get_payment_status(
        user_id=str(det_uuid(1)),
        txn_id=str(det_uuid(201)),
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["amount_paise"] == 500000
    assert res.data["amount_inr"] == 5000.0
    assert res.data["gateway"] == "razorpay"
    assert res.data["status"] == "failed"
    assert res.data["error_code"] == "BAD_REQUEST_ERROR"


@pytest.mark.asyncio
async def test_get_payment_status_by_gateway_payment_id(db_session):
    """Query payment status by gateway_payment_id string."""
    service = MockPaymentService(db_session)
    res = await service.get_payment_status(
        user_id=str(det_uuid(1)),
        payment_id="pay_K5x89Qwer123",
    )
    assert res.success is True
    assert res.data["gateway_payment_id"] == "pay_K5x89Qwer123"


@pytest.mark.asyncio
async def test_get_payment_status_unauthorized_user(db_session):
    """Cross-user isolation for payment status."""
    service = MockPaymentService(db_session)
    # Payment belongs to user_001. user_002 tries to inspect it:
    res = await service.get_payment_status(
        user_id=str(det_uuid(2)),
        txn_id=str(det_uuid(201)),
    )
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_get_payment_status_missing_arguments(db_session):
    """Missing both payment_id and txn_id returns INVALID_ARGUMENTS."""
    service = MockPaymentService(db_session)
    res = await service.get_payment_status(user_id=str(det_uuid(1)))
    assert res.success is False
    assert res.error.code == "INVALID_ARGUMENTS"
