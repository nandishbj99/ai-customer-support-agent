import uuid
from datetime import datetime
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
