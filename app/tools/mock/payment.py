from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Payment, Transaction
from app.tools.base import PaymentServiceBase
from app.tools.mock.utils import parse_identifier
from app.tools.schemas import ToolResult


class MockPaymentService(PaymentServiceBase):
    """Mock implementation of PaymentServiceBase querying local database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_payment_status(
        self,
        user_id: str,
        payment_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        if not payment_id and not txn_id:
            return ToolResult.fail(
                "INVALID_ARGUMENTS",
                "Either payment_id or txn_id must be provided to query payment status.",
            )

        parsed_user_id = parse_identifier(user_id)
        if not parsed_user_id:
            return ToolResult.fail("INVALID_USER_ID", f"Invalid user ID format: '{user_id}'")

        # Query payment with its associated transaction
        stmt = select(Payment).join(Transaction, Payment.txn_id == Transaction.id).options(
            selectinload(Payment.transaction)
        )

        conditions = []
        if payment_id:
            parsed_pay_id = parse_identifier(payment_id)
            if parsed_pay_id:
                conditions.append(Payment.id == parsed_pay_id)
            # Also allow searching by gateway_payment_id string (e.g. 'pay_K5x89Qwer123')
            conditions.append(Payment.gateway_payment_id == payment_id.strip())

        if txn_id:
            parsed_txn_id = parse_identifier(txn_id)
            if parsed_txn_id:
                conditions.append(Payment.txn_id == parsed_txn_id)

        stmt = stmt.where(or_(*conditions))
        result = await self.db.execute(stmt)
        payment = result.scalars().first()

        if not payment:
            # Check if payment exists anywhere to distinguish between not found and unauthorized
            direct_check_stmt = select(Payment).join(Transaction).where(or_(*conditions))
            direct_res = await self.db.execute(direct_check_stmt)
            any_pay = direct_res.scalars().first()
            if any_pay and any_pay.transaction.user_id != parsed_user_id:
                return ToolResult.fail(
                    "UNAUTHORIZED_ACCESS",
                    "Payment does not belong to the authenticated user.",
                )
            return ToolResult.fail("PAYMENT_NOT_FOUND", "Payment record not found.")

        # Check tenant isolation
        if payment.transaction.user_id != parsed_user_id:
            return ToolResult.fail(
                "UNAUTHORIZED_ACCESS",
                "Payment does not belong to the authenticated user.",
            )

        return ToolResult.ok(payment.to_dict())
