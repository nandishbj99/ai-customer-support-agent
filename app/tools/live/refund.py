from typing import Optional
from app.tools.base import RefundServiceBase
from app.tools.schemas import ToolResult


class RazorpayRefundService(RefundServiceBase):
    """Production live adapter integrating with Razorpay Refunds API."""

    def __init__(self, key_id: str = "", key_secret: str = ""):
        self.key_id = key_id
        self.key_secret = key_secret

    async def get_refund_status(
        self,
        user_id: str,
        refund_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        raise NotImplementedError("Razorpay live refund status lookup not configured.")

    async def initiate_refund(
        self,
        txn_id: str,
        user_id: str,
        amount_inr: float,
        reason: str,
        idempotency_key: Optional[str] = None,
    ) -> ToolResult:
        raise NotImplementedError("Razorpay live refund initiation not configured.")
