import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.fraud import MockFraudService


@pytest.mark.asyncio
async def test_tc07_check_fraud_status_flagged(db_session):
    """TC-07: checkFraudStatus for flagged transaction returns is_flagged=True, risk_score > 0.7."""
    service = MockFraudService(db_session)
    # user_002 owns txn_202 which has risk_score=0.87 and fraud_flagged=True
    res = await service.check_fraud_status(str(det_uuid(202)), str(det_uuid(2)))
    assert res.success is True
    assert res.data is not None
    assert res.data["is_flagged"] is True
    assert res.data["risk_score"] >= 0.7
    assert res.data["recommendation"] == "BLOCK_AND_ESCALATE"


@pytest.mark.asyncio
async def test_check_fraud_status_clean(db_session):
    """checkFraudStatus for clean transaction returns is_flagged=False."""
    service = MockFraudService(db_session)
    # user_001 owns txn_201 with risk_score=0.05
    res = await service.check_fraud_status(str(det_uuid(201)), str(det_uuid(1)))
    assert res.success is True
    assert res.data["is_flagged"] is False
    assert res.data["risk_score"] < 0.7
    assert res.data["recommendation"] == "ALLOW"


@pytest.mark.asyncio
async def test_check_fraud_status_unauthorized_user(db_session):
    """Cross-user tenant isolation check for fraud inspection."""
    service = MockFraudService(db_session)
    # txn_202 belongs to user_002. user_001 tries to access:
    res = await service.check_fraud_status(str(det_uuid(202)), str(det_uuid(1)))
    assert res.success is False
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_check_fraud_status_nonexistent_txn(db_session):
    """Nonexistent transaction returns TXN_NOT_FOUND."""
    service = MockFraudService(db_session)
    res = await service.check_fraud_status(str(det_uuid(9999)), str(det_uuid(1)))
    assert res.success is False
    assert res.error.code == "TXN_NOT_FOUND"
