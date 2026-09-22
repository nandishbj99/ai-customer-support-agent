import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.account import MockAccountService


@pytest.mark.asyncio
async def test_tc10_get_account_frozen(db_session):
    """TC-10: getAccount for frozen account returns status: 'frozen'."""
    service = MockAccountService(db_session)
    # user_005 has a frozen account
    res = await service.get_account(str(det_uuid(5)))
    assert res.success is True
    assert res.data is not None
    assert res.data["status"] == "frozen"
    assert res.data["balance_paise"] == 950000


@pytest.mark.asyncio
async def test_get_account_active(db_session):
    """getAccount for active account returns balance, type, and linked cards."""
    service = MockAccountService(db_session)
    # user_001 has active account with balance ₹3,200
    res = await service.get_account(str(det_uuid(1)))
    assert res.success is True
    assert res.data["status"] == "active"
    assert res.data["balance_inr"] == 3200.0
    assert len(res.data["linked_cards"]) == 1
    assert res.data["linked_cards"][0]["last4"] == "4242"


@pytest.mark.asyncio
async def test_get_account_balance(db_session):
    """getAccountBalance returns paise and inr values."""
    service = MockAccountService(db_session)
    res = await service.get_account_balance(str(det_uuid(2)))
    assert res.success is True
    assert res.data["balance_paise"] == 5000000
    assert res.data["balance_inr"] == 50000.0


@pytest.mark.asyncio
async def test_get_customer_profile(db_session):
    """getCustomerProfile returns customer details."""
    service = MockAccountService(db_session)
    res = await service.get_customer_profile(str(det_uuid(1)))
    assert res.success is True
    assert res.data["name"] == "Aarav Sharma"
    assert res.data["email"] == "aarav.sharma@example.in"
    assert res.data["kyc_status"] == "verified"


@pytest.mark.asyncio
async def test_get_account_nonexistent_user(db_session):
    """getAccount for nonexistent user returns ACCOUNT_NOT_FOUND."""
    service = MockAccountService(db_session)
    res = await service.get_account(str(det_uuid(9999)))
    assert res.success is False
    assert res.error.code == "ACCOUNT_NOT_FOUND"
