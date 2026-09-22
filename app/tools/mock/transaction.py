from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Transaction
from app.tools.base import TransactionServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockTransactionService(TransactionServiceBase):
    """Mock implementation of TransactionServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_transaction(self, txn_id: str, user_id: str) -> ToolResult:
        parsed_txn_id = parse_identifier(txn_id)
        parsed_user_id = parse_identifier(user_id)

        if not parsed_txn_id:
            return ToolResult.fail("INVALID_TRANSACTION_ID", f"Invalid transaction ID format: '{txn_id}'")
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        stmt = select(Transaction).where(Transaction.id == parsed_txn_id)
        result = await self.db.execute(stmt)
        txn = result.scalars().first()

        if not txn:
            return ToolResult.fail("TXN_NOT_FOUND", f"Transaction with ID '{txn_id}' not found.")

        # Cross-user tenant isolation check (TC-23)
        if txn.user_id != parsed_user_id:
            return ToolResult.fail(
                "UNAUTHORIZED_ACCESS",
                "Transaction does not belong to the authenticated user.",
                {"user_id": user_id, "txn_id": txn_id},
            )

        return ToolResult.ok(txn.to_dict())

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> ToolResult:
        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        base_stmt = select(Transaction).where(Transaction.user_id == parsed_user_id)
        if status:
            base_stmt = base_stmt.where(Transaction.status == status.lower())

        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Query paginated rows
        page_stmt = (
            base_stmt.order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        page_result = await self.db.execute(page_stmt)
        transactions = page_result.scalars().all()

        return ToolResult.ok(
            {
                "transactions": [t.to_dict() for t in transactions],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(transactions)) < total,
            }
        )
