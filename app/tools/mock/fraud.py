from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Transaction
from app.tools.base import FraudServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockFraudService(FraudServiceBase):
    """Mock implementation of FraudServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_fraud_status(self, txn_id: str, user_id: str) -> ToolResult:
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

        # Cross-user tenant isolation check
        if txn.user_id != parsed_user_id:
            return ToolResult.fail(
                "UNAUTHORIZED_ACCESS",
                "Transaction does not belong to the authenticated user.",
                {"user_id": user_id, "txn_id": txn_id},
            )

        risk_score = float(txn.risk_score) if txn.risk_score is not None else 0.0
        is_flagged = bool(txn.fraud_flagged or risk_score >= 0.7)

        recommendation = "ALLOW"
        if is_flagged:
            recommendation = "BLOCK_AND_ESCALATE" if risk_score >= 0.85 else "MANUAL_REVIEW"

        return ToolResult.ok(
            {
                "txn_id": str(txn.id),
                "user_id": str(txn.user_id),
                "is_flagged": is_flagged,
                "risk_score": risk_score,
                "transaction_status": txn.status,
                "failure_reason": txn.failure_reason,
                "recommendation": recommendation,
            }
        )
