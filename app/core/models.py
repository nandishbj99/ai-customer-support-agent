import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base

# Portable JSON type: JSONB on PostgreSQL, JSON on SQLite
JsonType = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tier: Mapped[str] = mapped_column(
        String(20), default="standard", nullable=False
    )  # standard, premium, vip
    kyc_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, verified, rejected
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    support_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="user", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(
        "ApprovalRequest", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "tier": self.tier,
            "kyc_status": self.kyc_status,
            "preferred_language": self.preferred_language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    balance_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, frozen, closed
    account_type: Mapped[str] = mapped_column(
        String(20), default="savings", nullable=False
    )  # savings, current
    linked_cards: Mapped[List[Dict[str, Any]]] = mapped_column(
        JsonType, default=list, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "balance_paise": self.balance_paise,
            "balance_inr": self.balance_paise / 100.0,
            "status": self.status,
            "account_type": self.account_type,
            "linked_cards": self.linked_cards or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failed, pending, blocked
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gateway_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    fraud_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    refunds: Mapped[List["Refund"]] = relationship(
        "Refund", back_populates="transaction", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="transaction", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount_paise": self.amount_paise,
            "amount_inr": self.amount_paise / 100.0,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "merchant_name": self.merchant_name,
            "payment_method": self.payment_method,
            "gateway_response": self.gateway_response,
            "fraud_flagged": self.fraud_flagged,
            "risk_score": float(self.risk_score) if self.risk_score is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    txn_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gateway: Mapped[str] = mapped_column(String(50), default="razorpay", nullable=False)
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # created, authorized, captured, refunded, failed
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="payments")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "txn_id": str(self.txn_id),
            "gateway": self.gateway,
            "gateway_payment_id": self.gateway_payment_id,
            "payment_method": self.payment_method,
            "amount_paise": self.amount_paise,
            "amount_inr": self.amount_paise / 100.0,
            "status": self.status,
            "error_code": self.error_code,
            "error_description": self.error_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    txn_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="initiated", nullable=False
    )  # initiated, processing, completed, failed, pending_approval
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="refunds")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "txn_id": str(self.txn_id),
            "amount_paise": self.amount_paise,
            "amount_inr": self.amount_paise / 100.0,
            "status": self.status,
            "reason": self.reason,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), default="low", nullable=False
    )  # low, medium, high, urgent
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False
    )  # open, pending, resolved, closed
    external_ticket_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="support_tickets")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "category": self.category,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "external_ticket_id": self.external_ticket_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tool_arguments: Mapped[Dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    context: Mapped[Dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED, ESCALATED, EXECUTED, FAILED
    amount_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    required_role: Mapped[str] = mapped_column(String(50), default="agent", nullable=False)
    priority: Mapped[int] = mapped_column(BigInteger, default=5, nullable=False)  # 1=critical, 10=low
    approver_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sla_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="approval_requests")
    audit_logs: Mapped[List["ApprovalAuditLog"]] = relationship(
        "ApprovalAuditLog",
        back_populates="approval_request",
        cascade="all, delete-orphan",
        order_by="ApprovalAuditLog.created_at",
    )

    def to_dict(self) -> Dict[str, Any]:
        c_at = self.__dict__.get("created_at")
        u_at = self.__dict__.get("updated_at")
        sla = self.__dict__.get("sla_expires_at")
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "tool_name": self.tool_name,
            "tool_arguments": self.tool_arguments,
            "context": self.context,
            "status": self.status,
            "amount_paise": self.amount_paise,
            "amount_inr": (self.amount_paise / 100.0) if self.amount_paise is not None else None,
            "required_role": self.required_role,
            "priority": self.priority,
            "approver_id": self.approver_id,
            "rejection_reason": self.rejection_reason,
            "sla_expires_at": sla.isoformat() if sla else None,
            "execution_result": self.execution_result,
            "created_at": c_at.isoformat() if c_at else None,
            "updated_at": u_at.isoformat() if u_at else None,
        }


class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    condition_type: Mapped[str] = mapped_column(
        String(50), default="amount_threshold", nullable=False
    )  # amount_threshold, always, parameter_match
    threshold_amount_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    condition_expression: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    required_role: Mapped[str] = mapped_column(String(50), default="agent", nullable=False)
    priority: Mapped[int] = mapped_column(BigInteger, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "rule_name": self.rule_name,
            "tool_name": self.tool_name,
            "condition_type": self.condition_type,
            "threshold_amount_paise": self.threshold_amount_paise,
            "threshold_amount_inr": (self.threshold_amount_paise / 100.0) if self.threshold_amount_paise is not None else None,
            "condition_expression": self.condition_expression,
            "required_role": self.required_role,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApprovalAuditLog(Base):
    __tablename__ = "approval_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    approval_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CREATED, ESCALATED, APPROVED, REJECTED, EXECUTED, FAILED
    actor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    approval_request: Mapped["ApprovalRequest"] = relationship(
        "ApprovalRequest", back_populates="audit_logs"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "approval_id": str(self.approval_id),
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False)  # SUCCESS, FAILURE, BLOCKED
    details: Mapped[Dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)

    def to_dict(self) -> Dict[str, Any]:
        t_stamp = self.__dict__.get("timestamp")
        return {
            "id": str(self.id),
            "timestamp": t_stamp.isoformat() if t_stamp else None,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
            "resource": self.resource,
            "action": self.action,
            "status": self.status,
            "details": self.details,
        }
