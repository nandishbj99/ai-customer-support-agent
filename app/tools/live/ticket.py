from app.tools.base import TicketServiceBase
from app.tools.schemas import ToolResult


class FreshdeskTicketService(TicketServiceBase):
    """Production live adapter integrating with Freshdesk Support API."""

    def __init__(self, domain: str = "", api_key: str = ""):
        self.domain = domain
        self.api_key = api_key

    async def create_support_ticket(
        self,
        user_id: str,
        category: str,
        description: str,
        priority: str = "low",
    ) -> ToolResult:
        raise NotImplementedError("Freshdesk live ticket creation not configured.")
