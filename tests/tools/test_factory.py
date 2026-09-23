import pytest
from app.tools.base import (
    AccountServiceBase,
    EscalationServiceBase,
    FraudServiceBase,
    NotificationServiceBase,
    PaymentServiceBase,
    RefundServiceBase,
    TicketServiceBase,
    TransactionServiceBase,
)
from app.tools.factory import ToolServiceFactory
from app.tools.live.account import CoreBankingAccountService
from app.tools.live.transaction import RazorpayTransactionService
from app.tools.mock.account import MockAccountService
from app.tools.mock.transaction import MockTransactionService


def test_tc14_factory_mock_mode(db_session):
    """TC-14: Factory creates mock adapters when TOOL_MODE=mock."""
    services = ToolServiceFactory.create_services(mode="mock", db_session=db_session)

    assert isinstance(services["transaction"], MockTransactionService)
    assert isinstance(services["transaction"], TransactionServiceBase)

    assert isinstance(services["account"], MockAccountService)
    assert isinstance(services["account"], AccountServiceBase)

    assert isinstance(services["payment"], PaymentServiceBase)
    assert isinstance(services["fraud"], FraudServiceBase)
    assert isinstance(services["refund"], RefundServiceBase)
    assert isinstance(services["ticket"], TicketServiceBase)
    assert isinstance(services["notification"], NotificationServiceBase)
    assert isinstance(services["escalation"], EscalationServiceBase)


def test_tc15_factory_live_mode():
    """TC-15: Factory creates live adapters when TOOL_MODE=live."""
    services = ToolServiceFactory.create_services(mode="live")

    assert isinstance(services["transaction"], RazorpayTransactionService)
    assert isinstance(services["transaction"], TransactionServiceBase)

    assert isinstance(services["account"], CoreBankingAccountService)
    assert isinstance(services["account"], AccountServiceBase)


def test_tc16_factory_hybrid_mode(db_session):
    """TC-16: Factory handles hybrid mode with per-tool overrides."""
    overrides = {
        "transaction": "live",
        "account": "mock",
    }
    services = ToolServiceFactory.create_services(
        mode="hybrid",
        db_session=db_session,
        overrides=overrides,
    )

    # Overridden to live
    assert isinstance(services["transaction"], RazorpayTransactionService)
    # Kept as mock
    assert isinstance(services["account"], MockAccountService)
