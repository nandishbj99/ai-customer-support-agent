from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Account, User
from app.tools.base import AccountServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockAccountService(AccountServiceBase):
    """Mock implementation of AccountServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_account(self, user_id: str) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        stmt = select(Account).where(Account.user_id == parsed_user_id)
        result = await self.db.execute(stmt)
        account = result.scalars().first()

        if not account:
            return ToolResult.fail("ACCOUNT_NOT_FOUND", f"No account found for user '{user_id}'.")

        return ToolResult.ok(account.to_dict())

    async def get_account_balance(self, user_id: str) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        stmt = select(Account).where(Account.user_id == parsed_user_id)
        result = await self.db.execute(stmt)
        account = result.scalars().first()

        if not account:
            return ToolResult.fail("ACCOUNT_NOT_FOUND", f"No account found for user '{user_id}'.")

        return ToolResult.ok(
            {
                "account_id": str(account.id),
                "user_id": str(account.user_id),
                "balance_paise": account.balance_paise,
                "balance_inr": account.balance_paise / 100.0,
                "status": account.status,
                "account_type": account.account_type,
            }
        )

    async def get_customer_profile(self, user_id: str) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        stmt = select(User).where(User.id == parsed_user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            return ToolResult.fail("USER_NOT_FOUND", f"User profile not found for ID '{user_id}'.")

        return ToolResult.ok(user.to_dict())
