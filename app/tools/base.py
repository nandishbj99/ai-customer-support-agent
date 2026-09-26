from abc import ABC, abstractmethod
from typing import Optional
from app.tools.schemas import ToolResult


class TransactionServiceBase(ABC):
    """Abstract interface for transaction operations."""

    @abstractmethod
    async def get_transaction(self, txn_id: str, user_id: str) -> ToolResult:
        """Fetch details of a single transaction for a given user."""
        ...

    @abstractmethod
    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> ToolResult:
        """Fetch paginated transaction history for a user."""
        ...


class AccountServiceBase(ABC):
    """Abstract interface for customer account and profile operations."""

    @abstractmethod
    async def get_account(self, user_id: str) -> ToolResult:
        """Fetch primary account status, type, and linked cards for a user."""
        ...

    @abstractmethod
    async def get_account_balance(self, user_id: str) -> ToolResult:
        """Fetch balance details for a user's active account."""
        ...

    @abstractmethod
    async def get_customer_profile(self, user_id: str) -> ToolResult:
        """Fetch customer profile, KYC status, and preferences."""
        ...


class PaymentServiceBase(ABC):
    """Abstract interface for payment gateway operations."""

    @abstractmethod
    async def get_payment_status(
        self,
        user_id: str,
        payment_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        """Check gateway status and error logs for a payment."""
        ...


class FraudServiceBase(ABC):
    """Abstract interface for fraud detection and risk scoring."""

    @abstractmethod
    async def check_fraud_status(self, txn_id: str, user_id: str) -> ToolResult:
        """Evaluate whether a transaction is flagged for fraud and get risk score."""
        ...


class RefundServiceBase(ABC):
    """Abstract interface for refund lifecycle operations."""

    @abstractmethod
    async def get_refund_status(
        self,
        user_id: str,
        refund_id: Optional[str] = None,
        txn_id: Optional[str] = None,
    ) -> ToolResult:
        """Check status of a refund by refund ID or original transaction ID."""
        ...

    @abstractmethod
    async def initiate_refund(
        self,
        txn_id: str,
        user_id: str,
        amount_inr: float,
        reason: str,
        idempotency_key: Optional[str] = None,
    ) -> ToolResult:
        """Initiate a refund. Auto-approves under ₹10,000, routes to HITL if higher."""
        ...


class TicketServiceBase(ABC):
    """Abstract interface for support ticketing."""

    @abstractmethod
    async def create_support_ticket(
        self,
        user_id: str,
        category: str,
        description: str,
        priority: str = "low",
    ) -> ToolResult:
        """Create a persistent customer support ticket."""
        ...


class NotificationServiceBase(ABC):
    """Abstract interface for customer notifications (SMS, Email, Push)."""

    @abstractmethod
    async def send_notification(
        self,
        user_id: str,
        channel: str,
        message: str,
    ) -> ToolResult:
        """Send an outbound notification to the customer."""
        ...


class EscalationServiceBase(ABC):
    """Abstract interface for routing conversations to human agents (HITL)."""

    @abstractmethod
    async def escalate_to_human_agent(
        self,
        user_id: str,
        reason: str,
        conversation_summary: str,
        priority: str = "medium",
    ) -> ToolResult:
        """Escalate ticket and context to the human support queue."""
        ...


class PolicyServiceBase(ABC):
    """Abstract interface for knowledge base policy and regulation lookup."""

    @abstractmethod
    async def search_policy(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
    ) -> ToolResult:
        """Search banking guidelines, FAQs, chargeback rules, and RBI policies."""
        ...
