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
from app.tools.schemas import ToolResult


def test_cannot_instantiate_abcs_directly():
    """Verify that ABCs cannot be instantiated without concrete implementations."""
    with pytest.raises(TypeError):
        TransactionServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        AccountServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        PaymentServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        FraudServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        RefundServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        TicketServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        NotificationServiceBase()  # type: ignore

    with pytest.raises(TypeError):
        EscalationServiceBase()  # type: ignore


@pytest.mark.asyncio
async def test_concrete_mock_implementation_compliance():
    """Verify that a minimal concrete class implements the interface properly."""
    class DummyTransactionService(TransactionServiceBase):
        async def get_transaction(self, txn_id: str, user_id: str) -> ToolResult:
            return ToolResult.ok({"txn_id": txn_id, "user_id": user_id})

        async def get_transaction_history(
            self, user_id: str, limit: int = 10, offset: int = 0, status=None
        ) -> ToolResult:
            return ToolResult.ok({"transactions": [], "total": 0})

    svc = DummyTransactionService()
    res = await svc.get_transaction("txn_1", "user_1")
    assert res.success is True
    assert res.data["txn_id"] == "txn_1"
