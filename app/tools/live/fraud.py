from app.tools.base import FraudServiceBase
from app.tools.schemas import ToolResult


class FraudDetectionMLService(FraudServiceBase):
    """Production live adapter integrating with internal Fraud Detection ML model endpoint."""

    def __init__(self, endpoint_url: str = ""):
        self.endpoint_url = endpoint_url

    async def check_fraud_status(self, txn_id: str, user_id: str) -> ToolResult:
        raise NotImplementedError("Internal ML fraud detection service not configured.")
