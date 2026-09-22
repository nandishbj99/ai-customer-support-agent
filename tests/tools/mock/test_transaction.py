import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.transaction import MockTransactionService


@pytest.mark.asyncio
async def test_tc05_get_transaction_valid(db_session):
    """TC-05: getTransaction with valid txn_id returns ToolResult(success=True) with transaction data."""
    service = MockTransactionService(db_session)
    # user_001 owns txn_201
    res = await service.get_transaction(str(det_uuid(201)), str(det_uuid(1)))
    assert res.success is True
    assert res.data is not None
    assert res.data["id"] == str(det_uuid(201))
    assert res.data["amount_paise"] == 500000
    assert res.data["amount_inr"] == 5000.0
    assert res.data["status"] == "failed"
    assert res.data["failure_reason"] == "INSUFFICIENT_FUNDS"


@pytest.mark.asyncio
async def test_tc06_get_transaction_nonexistent(db_session):
    """TC-06: getTransaction with non-existent txn_id returns ToolResult(success=False, TXN_NOT_FOUND)."""
    service = MockTransactionService(db_session)
    non_existent = str(det_uuid(9999))
    res = await service.get_transaction(non_existent, str(det_uuid(1)))
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "TXN_NOT_FOUND"


@pytest.mark.asyncio
async def test_tc23_cross_user_isolation(db_session):
    """TC-23: User A tries to access User B's transaction -> returns UNAUTHORIZED_ACCESS."""
    service = MockTransactionService(db_session)
    # txn_201 belongs to user_001. user_002 tries to access it:
    res = await service.get_transaction(str(det_uuid(201)), str(det_uuid(2)))
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "UNAUTHORIZED_ACCESS"


@pytest.mark.asyncio
async def test_tc20_get_transaction_history_pagination(db_session):
    """TC-20: getTransactionHistory with pagination returns correct page size and has_more flag."""
    service = MockTransactionService(db_session)
    # user_007 has 3 seeded transactions (207, 208, 209)
    res_p1 = await service.get_transaction_history(str(det_uuid(7)), limit=2, offset=0)
    assert res_p1.success is True
    assert res_p1.data is not None
    assert res_p1.data["total"] == 3
    assert len(res_p1.data["transactions"]) == 2
    assert res_p1.data["has_more"] is True

    res_p2 = await service.get_transaction_history(str(det_uuid(7)), limit=2, offset=2)
    assert res_p2.success is True
    assert len(res_p2.data["transactions"]) == 1
    assert res_p2.data["has_more"] is False


@pytest.mark.asyncio
async def test_get_transaction_history_filtered_status(db_session):
    """Filter transaction history by status."""
    service = MockTransactionService(db_session)
    # user_007: 2 success, 1 failed
    res_failed = await service.get_transaction_history(str(det_uuid(7)), status="failed")
    assert res_failed.success is True
    assert res_failed.data["total"] == 1
    assert res_failed.data["transactions"][0]["status"] == "failed"
