import uuid
from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.models import Refund, Transaction
from app.tools.base import RefundServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockRefundService(RefundServiceBase):
    """Mock implementation of RefundServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_refund_status(
        self,
        user_id: str,
        refund_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        if not refund_id and not txn_id:
            return ToolResult.fail(
                "INVALID_ARGUMENTS",
                "Either refund_id or txn_id must be provided to query refund status.",
            )

        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        stmt = select(Refund).join(Transaction, Refund.txn_id == Transaction.id).options(
            selectinload(Refund.transaction)
        )

        conditions = []
        if refund_id:
            parsed_ref_id = parse_identifier(refund_id)
            if parsed_ref_id:
                conditions.append(Refund.id == parsed_ref_id)
        if txn_id:
            parsed_txn_id = parse_identifier(txn_id)
            if parsed_txn_id:
                conditions.append(Refund.txn_id == parsed_txn_id)

        stmt = stmt.where(or_(*conditions))
        result = await self.db.execute(stmt)
        refund = result.scalars().first()

        if not refund:
            return ToolResult.fail("REFUND_NOT_FOUND", "Refund record not found.")

        # Check tenant isolation
        if refund.transaction.user_id != parsed_user_id:
            return ToolResult.fail(
                "UNAUTHORIZED_ACCESS",
                "Refund does not belong to the authenticated user.",
            )

        return ToolResult.ok(refund.to_dict())

    async def initiate_refund(
        self,
        txn_id: str,
        user_id: str,
        amount_inr: float,
        reason: str,
        idempotency_key: Optional[str] = None,
    ) -> ToolResult:
        parsed_txn_id = parse_identifier(txn_id)
        parsed_user_id = parse_identifier(user_id)

        if not parsed_txn_id:
            return ToolResult.fail("INVALID_TRANSACTION_ID", f"Invalid transaction ID format: '{txn_id}'")
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        # Verify transaction
        stmt = select(Transaction).where(Transaction.id == parsed_txn_id)
        result = await self.db.execute(stmt)
        txn = result.scalars().first()

        if not txn:
            return ToolResult.fail("TXN_NOT_FOUND", f"Transaction with ID '{txn_id}' not found.")

        # Enforce tenant isolation
        if txn.user_id != parsed_user_id:
            return ToolResult.fail(
                "UNAUTHORIZED_ACCESS",
                "Transaction does not belong to the authenticated user.",
            )

        # Check idempotency replay
        if idempotency_key:
            idem_stmt = select(Refund).where(Refund.idempotency_key == idempotency_key.strip())
            idem_res = await self.db.execute(idem_stmt)
            existing_refund = idem_res.scalars().first()
            if existing_refund:
                return ToolResult.ok(
                    {
                        **existing_refund.to_dict(),
                        "is_idempotent_replay": True,
                    }
                )

        amount_paise = int(round(amount_inr * 100))
        if amount_paise <= 0:
            return ToolResult.fail("INVALID_AMOUNT", "Refund amount must be strictly greater than 0.")

        if amount_paise > txn.amount_paise:
            return ToolResult.fail(
                "REFUND_EXCEEDS_TRANSACTION",
                f"Refund amount (₹{amount_inr:,.2f}) cannot exceed transaction amount (₹{txn.amount_paise / 100:,.2f}).",
            )

        # Check HITL Approval Threshold (₹10,000 = 1,000,000 paise)
        requires_hitl = amount_paise > settings.REFUND_HITL_THRESHOLD_PAISE
        status = "pending_approval" if requires_hitl else "processing"

        new_refund = Refund(
            id=uuid.uuid4(),
            txn_id=txn.id,
            amount_paise=amount_paise,
            status=status,
            reason=reason,
            idempotency_key=idempotency_key,
        )
        self.db.add(new_refund)
        await self.db.flush()

        msg = (
            f"Refund of ₹{amount_inr:,.2f} exceeds ₹10,000 threshold and has been submitted to supervisor queue for approval."
            if requires_hitl
            else f"Refund of ₹{amount_inr:,.2f} initiated successfully and is now processing."
        )

        return ToolResult.ok(
            {
                "refund_id": str(new_refund.id),
                "txn_id": str(txn.id),
                "amount_paise": amount_paise,
                "amount_inr": amount_inr,
                "status": status,
                "requires_hitl": requires_hitl,
                "message": msg,
            }
        )
