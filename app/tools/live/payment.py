from typing import Optional
from app.tools.base import PaymentServiceBase
from app.tools.schemas import ToolResult


class RazorpayPaymentService(PaymentServiceBase):
    """Production live adapter integrating with Razorpay Payments API."""

    def __init__(self, key_id: str = "", key_secret: str = ""):
        self.key_id = key_id
        self.key_secret = key_secret

    async def get_payment_status(
        self,
        user_id: str,
        payment_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        raise NotImplementedError("Razorpay live payment status lookup not configured.")
