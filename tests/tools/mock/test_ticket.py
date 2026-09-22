import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.ticket import MockTicketService


@pytest.mark.asyncio
async def test_create_support_ticket_success(db_session):
    """create_support_ticket creates open ticket in database."""
    service = MockTicketService(db_session)
    res = await service.create_support_ticket(
        user_id=str(det_uuid(1)),
        category="TRANSACTION_DISPUTE",
        description="Duplicate charge observed on merchant POS terminal.",
        priority="high",
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["category"] == "TRANSACTION_DISPUTE"
    assert res.data["status"] == "open"
    assert res.data["priority"] == "high"
    assert "external_ticket_id" in res.data


@pytest.mark.asyncio
async def test_create_support_ticket_nonexistent_user(db_session):
    """create_support_ticket for nonexistent user returns USER_NOT_FOUND."""
    service = MockTicketService(db_session)
    res = await service.create_support_ticket(
        user_id=str(det_uuid(9999)),
        category="GENERAL_INQUIRY",
        description="Inquiry about reward points program.",
    )
    assert res.success is False
    assert res.error.code == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_support_ticket_invalid_user_id(db_session):
    """create_support_ticket with empty user_id returns INVALID_USER_ID."""
    service = MockTicketService(db_session)
    res = await service.create_support_ticket(
        user_id="",
        category="GENERAL",
        description="Test description.",
    )
    assert res.success is False
    assert res.error.code == "INVALID_USER_ID"
