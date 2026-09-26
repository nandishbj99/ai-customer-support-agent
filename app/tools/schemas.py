from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Standard Output Wrapper (ADR-04)
# ============================================================================

class ToolError(BaseModel):
    code: str = Field(..., description="Machine-readable semantic error code (e.g., TXN_NOT_FOUND, RATE_LIMITED)")
    message: str = Field(..., description="Human-readable explanation of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra error details or telemetry")


class ToolResult(BaseModel):
    success: bool = Field(..., description="True if tool execution succeeded, False otherwise")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Result payload if success=True")
    error: Optional[ToolError] = Field(default=None, description="Error payload if success=False")

    def is_success(self) -> bool:
        return bool(self.success)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def ok(cls, data: Dict[str, Any]) -> "ToolResult":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> "ToolResult":
        return cls(success=False, data=None, error=ToolError(code=code, message=message, details=details))


# ============================================================================
# Core Read Tool Inputs
# ============================================================================

class GetTransactionInput(BaseModel):
    txn_id: str = Field(..., min_length=1, description="The unique UUID or identifier of the transaction")
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID for ownership validation")


class GetAccountInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")


class GetAccountBalanceInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")


class GetCustomerProfileInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")


class GetPaymentStatusInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    payment_id: Optional[str] = Field(default=None, description="Payment gateway transaction ID if available")
    txn_id: Optional[str] = Field(default=None, description="Internal transaction UUID if payment_id is unknown")


# ============================================================================
# Investigation Tool Inputs
# ============================================================================

class CheckFraudStatusInput(BaseModel):
    txn_id: str = Field(..., min_length=1, description="Transaction UUID to inspect for fraud alerts")
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")


class GetRefundStatusInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    refund_id: Optional[str] = Field(default=None, description="The unique refund UUID if known")
    txn_id: Optional[str] = Field(default=None, description="The transaction UUID associated with the refund")


class GetTransactionHistoryInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    limit: int = Field(default=10, ge=1, le=50, description="Max number of transactions to retrieve (1-50)")
    offset: int = Field(default=0, ge=0, description="Pagination offset index")
    status: Optional[Literal["success", "failed", "pending", "blocked"]] = Field(
        default=None, description="Filter transactions by status"
    )


# ============================================================================
# Write / Mutation Tool Inputs
# ============================================================================

class InitiateRefundInput(BaseModel):
    txn_id: str = Field(..., min_length=1, description="Transaction UUID for which to issue a refund")
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    amount_inr: float = Field(..., gt=0, description="Refund amount in Indian Rupees (e.g. 500.00)")
    reason: str = Field(..., min_length=5, description="Clear business reason for initiating the refund")
    idempotency_key: Optional[str] = Field(
        default=None, description="Optional unique key to ensure idempotent refund processing during retries"
    )

    @field_validator("amount_inr")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Refund amount must be strictly greater than 0")
        if v > 1_000_000.0:
            raise ValueError("Refund amount exceeds maximum permissible limit of ₹1,000,000")
        return round(v, 2)


class CreateSupportTicketInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    category: str = Field(..., min_length=2, description="Issue category (e.g., PAYMENT_FAILURE, ACCOUNT_LOCKED, DISPUTE)")
    description: str = Field(..., min_length=10, description="Detailed problem description")
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="low", description="Priority level of the support ticket"
    )


class SendNotificationInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    channel: Literal["sms", "email", "push", "in_app"] = Field(..., description="Delivery channel")
    message: str = Field(..., min_length=1, max_length=1000, description="Notification message text")


# ============================================================================
# Delegation & Orchestrator Tool Inputs
# ============================================================================

class SearchPolicyInput(BaseModel):
    query: str = Field(..., min_length=3, description="Search query regarding fintech policies, FAQs, or rules")
    category: Optional[str] = Field(default=None, description="Optional policy category filter")


class EscalateToHumanAgentInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="The authenticated user's ID")
    reason: str = Field(..., min_length=5, description="Reason why human escalation is required")
    conversation_summary: str = Field(..., min_length=10, description="Contextual summary of the conversation so far")
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        default="medium", description="Priority level for agent routing"
    )
