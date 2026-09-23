from app.tools.base import AccountServiceBase
from app.tools.schemas import ToolResult


class CoreBankingAccountService(AccountServiceBase):
    """Production live adapter integrating with Core Banking System (CBS) APIs."""

    def __init__(self, api_url: str = "", api_key: str = ""):
        self.api_url = api_url
        self.api_key = api_key

    async def get_account(self, user_id: str) -> ToolResult:
        raise NotImplementedError("Core banking live account lookup not configured.")

    async def get_account_balance(self, user_id: str) -> ToolResult:
        raise NotImplementedError("Core banking live balance lookup not configured.")

    async def get_customer_profile(self, user_id: str) -> ToolResult:
        raise NotImplementedError("Core banking live customer profile lookup not configured.")
