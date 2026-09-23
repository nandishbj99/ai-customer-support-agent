from typing import Optional
from app.tools.base import TransactionServiceBase
from app.tools.schemas import ToolResult


class RazorpayTransactionService(TransactionServiceBase):
    """Production live adapter integrating with Razorpay Payments API."""

    def __init__(self, key_id: str = "", key_secret: str = ""):
        self.key_id = key_id
        self.key_secret = key_secret

    async def get_transaction(self, txn_id: str, user_id: str) -> ToolResult:
        raise NotImplementedError("Razorpay live transaction lookup not configured.")

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> ToolResult:
        raise NotImplementedError("Razorpay live transaction history not configured.")
