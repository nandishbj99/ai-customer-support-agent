import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import SupportTicket, User
from app.tools.base import TicketServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockTicketService(TicketServiceBase):
    """Mock implementation of TicketServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_support_ticket(
        self,
        user_id: str,
        category: str,
        description: str,
        priority: str = "low",
    ) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        # Verify user exists
        stmt = select(User).where(User.id == parsed_user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        if not user:
            return ToolResult.fail("USER_NOT_FOUND", f"Cannot create ticket: user '{user_id}' does not exist.")

        ticket_id = uuid.uuid4()
        external_id = f"FD-MOCK-{ticket_id.hex[:8].upper()}"

        new_ticket = SupportTicket(
            id=ticket_id,
            user_id=parsed_user_id,
            category=category.upper().strip(),
            description=description.strip(),
            priority=priority.lower().strip(),
            status="open",
            external_ticket_id=external_id,
        )
        self.db.add(new_ticket)
        await self.db.flush()

        return ToolResult.ok(new_ticket.to_dict())
