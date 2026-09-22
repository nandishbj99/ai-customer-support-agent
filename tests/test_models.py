import uuid
from datetime import datetime, timezone
import pytest

from app.core.models import Account, Payment, Refund, SupportTicket, Transaction, User


def test_user_model_instantiation():
    u = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        phone="+919876543210",
        tier="standard",
        kyc_status="verified",
        preferred_language="en",
    )
    d = u.to_dict()
    assert d["name"] == "Test User"
    assert d["email"] == "test@example.com"
    assert d["tier"] == "standard"
    assert d["kyc_status"] == "verified"


def test_account_model_conversion():
    uid = uuid.uuid4()
    acc = Account(
        id=uuid.uuid4(),
        user_id=uid,
        balance_paise=500000,
        status="active",
        account_type="savings",
        linked_cards=[{"last4": "1234"}],
    )
    d = acc.to_dict()
    assert d["balance_paise"] == 500000
    assert d["balance_inr"] == 5000.0
    assert d["status"] == "active"
    assert len(d["linked_cards"]) == 1


def test_transaction_model_conversion():
    uid = uuid.uuid4()
    txn = Transaction(
        id=uuid.uuid4(),
        user_id=uid,
        amount_paise=150000,
        status="failed",
        failure_reason="INSUFFICIENT_FUNDS",
        merchant_name="Test Merchant",
        fraud_flagged=False,
        risk_score=0.15,
    )
    d = txn.to_dict()
    assert d["amount_paise"] == 150000
    assert d["amount_inr"] == 1500.0
    assert d["status"] == "failed"
    assert d["fraud_flagged"] is False
    assert d["risk_score"] == 0.15


def test_refund_model_conversion():
    tx_id = uuid.uuid4()
    ref = Refund(
        id=uuid.uuid4(),
        txn_id=tx_id,
        amount_paise=50000,
        status="initiated",
        reason="Customer cancellation",
        idempotency_key="ref_123",
    )
    d = ref.to_dict()
    assert d["amount_paise"] == 50000
    assert d["amount_inr"] == 500.0
    assert d["idempotency_key"] == "ref_123"


def test_payment_and_ticket_models():
    tx_id = uuid.uuid4()
    pay = Payment(
        id=uuid.uuid4(),
        txn_id=tx_id,
        gateway="razorpay",
        gateway_payment_id="pay_999",
        payment_method="upi",
        amount_paise=100000,
        status="captured",
    )
    d_pay = pay.to_dict()
    assert d_pay["gateway_payment_id"] == "pay_999"
    assert d_pay["amount_inr"] == 1000.0

    u_id = uuid.uuid4()
    ticket = SupportTicket(
        id=uuid.uuid4(),
        user_id=u_id,
        category="BILLING",
        description="Duplicate billing incident",
        priority="high",
        status="open",
    )
    d_ticket = ticket.to_dict()
    assert d_ticket["category"] == "BILLING"
    assert d_ticket["priority"] == "high"
