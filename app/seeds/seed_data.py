import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, async_session_factory, engine
from app.core.models import Account, Payment, Refund, SupportTicket, Transaction, User


def det_uuid(prefix_int: int) -> uuid.UUID:
    """Generate deterministic UUID from an integer (e.g. 1 -> 00000000-0000-0000-0000-000000000001)."""
    return uuid.UUID(f"{prefix_int:032x}")


SEED_USERS = [
    # S-01: User with failed txn due to insufficient balance
    {
        "id": det_uuid(1),
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.in",
        "phone": "+919876543201",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-02: User with blocked transaction due to high fraud risk
    {
        "id": det_uuid(2),
        "name": "Priya Patel",
        "email": "priya.patel@example.in",
        "phone": "+919876543202",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-03: User with successfully refunded transaction
    {
        "id": det_uuid(3),
        "name": "Rohan Verma",
        "email": "rohan.verma@example.in",
        "phone": "+919876543203",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-04: User requesting large refund (> ₹10,000 HITL threshold)
    {
        "id": det_uuid(4),
        "name": "Sneha Reddy",
        "email": "sneha.reddy@example.in",
        "phone": "+919876543204",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-05: User with frozen account
    {
        "id": det_uuid(5),
        "name": "Vikram Singh",
        "email": "vikram.singh@example.in",
        "phone": "+919876543205",
        "tier": "standard",
        "kyc_status": "pending",
        "preferred_language": "en",
    },
    # S-06: User with pending transaction (gateway timeout)
    {
        "id": det_uuid(6),
        "name": "Ananya Iyer",
        "email": "ananya.iyer@example.in",
        "phone": "+919876543206",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-07: User with multiple transactions for pagination
    {
        "id": det_uuid(7),
        "name": "Karan Malhotra",
        "email": "karan.malhotra@example.in",
        "phone": "+919876543207",
        "tier": "premium",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-08: VIP User
    {
        "id": det_uuid(8),
        "name": "Sunita Rao",
        "email": "sunita.rao@example.in",
        "phone": "+919876543208",
        "tier": "vip",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-09: User with open dispute ticket
    {
        "id": det_uuid(9),
        "name": "Devendra Joshi",
        "email": "devendra.joshi@example.in",
        "phone": "+919876543209",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-10: User with pending refund awaiting approval
    {
        "id": det_uuid(10),
        "name": "Meera Nambiar",
        "email": "meera.nambiar@example.in",
        "phone": "+919876543210",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    # S-11 to S-15: Additional realistic scenarios
    {
        "id": det_uuid(11),
        "name": "Aditya Sengupta",
        "email": "aditya.sengupta@example.in",
        "phone": "+919876543211",
        "tier": "standard",
        "kyc_status": "rejected",
        "preferred_language": "en",
    },
    {
        "id": det_uuid(12),
        "name": "Kavita Nair",
        "email": "kavita.nair@example.in",
        "phone": "+919876543212",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    {
        "id": det_uuid(13),
        "name": "Rajesh Gupta",
        "email": "rajesh.gupta@example.in",
        "phone": "+919876543213",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    {
        "id": det_uuid(14),
        "name": "Pooja Das",
        "email": "pooja.das@example.in",
        "phone": "+919876543214",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
    {
        "id": det_uuid(15),
        "name": "Tarun Mehra",
        "email": "tarun.mehra@example.in",
        "phone": "+919876543215",
        "tier": "standard",
        "kyc_status": "verified",
        "preferred_language": "en",
    },
]

SEED_ACCOUNTS = [
    # S-01: Balance ₹3,200 (320,000 paise)
    {
        "id": det_uuid(101),
        "user_id": det_uuid(1),
        "balance_paise": 320000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [{"last4": "4242", "network": "visa", "type": "debit"}],
    },
    # S-02: Balance ₹50,000 (5,000,000 paise)
    {
        "id": det_uuid(102),
        "user_id": det_uuid(2),
        "balance_paise": 5000000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [{"last4": "8888", "network": "mastercard", "type": "credit"}],
    },
    # S-03: Balance ₹12,500
    {
        "id": det_uuid(103),
        "user_id": det_uuid(3),
        "balance_paise": 1250000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [{"last4": "1111", "network": "rupay", "type": "debit"}],
    },
    # S-04: Balance ₹80,000
    {
        "id": det_uuid(104),
        "user_id": det_uuid(4),
        "balance_paise": 8000000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [{"last4": "3333", "network": "visa", "type": "debit"}],
    },
    # S-05: FROZEN account
    {
        "id": det_uuid(105),
        "user_id": det_uuid(5),
        "balance_paise": 950000,
        "status": "frozen",
        "account_type": "savings",
        "linked_cards": [{"last4": "9999", "network": "visa", "type": "debit"}],
    },
    # S-06: Active
    {
        "id": det_uuid(106),
        "user_id": det_uuid(6),
        "balance_paise": 450000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    # S-07: Balance ₹150,000
    {
        "id": det_uuid(107),
        "user_id": det_uuid(7),
        "balance_paise": 15000000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [{"last4": "7777", "network": "visa", "type": "credit"}],
    },
    # S-08: VIP Balance ₹500,000
    {
        "id": det_uuid(108),
        "user_id": det_uuid(8),
        "balance_paise": 50000000,
        "status": "active",
        "account_type": "current",
        "linked_cards": [{"last4": "0007", "network": "amex", "type": "credit"}],
    },
    # S-09 to S-15
    {
        "id": det_uuid(109),
        "user_id": det_uuid(9),
        "balance_paise": 1800000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(110),
        "user_id": det_uuid(10),
        "balance_paise": 2200000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(111),
        "user_id": det_uuid(11),
        "balance_paise": 0,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(112),
        "user_id": det_uuid(12),
        "balance_paise": 640000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(113),
        "user_id": det_uuid(13),
        "balance_paise": 3100000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(114),
        "user_id": det_uuid(14),
        "balance_paise": 100000,
        "status": "active",
        "account_type": "savings",
        "linked_cards": [],
    },
    {
        "id": det_uuid(115),
        "user_id": det_uuid(15),
        "balance_paise": 0,
        "status": "closed",
        "account_type": "savings",
        "linked_cards": [],
    },
]

now = datetime.now(timezone.utc)

SEED_TRANSACTIONS = [
    # S-01: ₹5,000 FAILED due to insufficient funds (balance is only ₹3,200)
    {
        "id": det_uuid(201),
        "user_id": det_uuid(1),
        "amount_paise": 500000,
        "status": "failed",
        "failure_reason": "INSUFFICIENT_FUNDS",
        "merchant_name": "Flipkart Internet Pvt Ltd",
        "payment_method": "upi",
        "gateway_response": {"code": "PAYMENT_DECLINED", "reason": "Insufficient balance in linked account"},
        "fraud_flagged": False,
        "risk_score": 0.05,
        "created_at": now - timedelta(hours=2),
    },
    # S-02: ₹25,000 BLOCKED due to fraud risk (risk_score 0.87)
    {
        "id": det_uuid(202),
        "user_id": det_uuid(2),
        "amount_paise": 2500000,
        "status": "blocked",
        "failure_reason": "FRAUD_DETECTION_TRIGGERED",
        "merchant_name": "CryptoExchange Global",
        "payment_method": "credit_card",
        "gateway_response": {"code": "SECURITY_BLOCK", "risk_rating": "HIGH"},
        "fraud_flagged": True,
        "risk_score": 0.87,
        "created_at": now - timedelta(hours=5),
    },
    # S-03: ₹1,200 refunded
    {
        "id": det_uuid(203),
        "user_id": det_uuid(3),
        "amount_paise": 120000,
        "status": "success",
        "failure_reason": None,
        "merchant_name": "Swiggy Food Delivery",
        "payment_method": "upi",
        "gateway_response": {"code": "PAYMENT_SUCCESS", "gateway_txn": "pay_swiggy_123"},
        "fraud_flagged": False,
        "risk_score": 0.02,
        "created_at": now - timedelta(days=1),
    },
    # S-04: ₹15,000 FAILED transaction (Large amount > ₹10K HITL threshold)
    {
        "id": det_uuid(204),
        "user_id": det_uuid(4),
        "amount_paise": 1500000,
        "status": "failed",
        "failure_reason": "GATEWAY_TIMEOUT",
        "merchant_name": "MakeMyTrip Flights",
        "payment_method": "net_banking",
        "gateway_response": {"code": "BANK_SERVER_UNRESPONSIVE"},
        "fraud_flagged": False,
        "risk_score": 0.12,
        "created_at": now - timedelta(hours=1),
    },
    # S-06: ₹3,500 PENDING
    {
        "id": det_uuid(206),
        "user_id": det_uuid(6),
        "amount_paise": 350000,
        "status": "pending",
        "failure_reason": None,
        "merchant_name": "Amazon India",
        "payment_method": "upi",
        "gateway_response": {"code": "AWAITING_BANK_CONFIRMATION"},
        "fraud_flagged": False,
        "risk_score": 0.08,
        "created_at": now - timedelta(minutes=15),
    },
    # S-07: Multiple txns for user 7 (pagination test)
    {
        "id": det_uuid(207),
        "user_id": det_uuid(7),
        "amount_paise": 45000,
        "status": "success",
        "failure_reason": None,
        "merchant_name": "Uber India",
        "payment_method": "upi",
        "gateway_response": {"code": "SUCCESS"},
        "fraud_flagged": False,
        "risk_score": 0.01,
        "created_at": now - timedelta(hours=10),
    },
    {
        "id": det_uuid(208),
        "user_id": det_uuid(7),
        "amount_paise": 820000,
        "status": "success",
        "failure_reason": None,
        "merchant_name": "Zara Retail",
        "payment_method": "credit_card",
        "gateway_response": {"code": "SUCCESS"},
        "fraud_flagged": False,
        "risk_score": 0.03,
        "created_at": now - timedelta(days=2),
    },
    {
        "id": det_uuid(209),
        "user_id": det_uuid(7),
        "amount_paise": 150000,
        "status": "failed",
        "failure_reason": "INVALID_OTP",
        "merchant_name": "BookMyShow",
        "payment_method": "debit_card",
        "gateway_response": {"code": "AUTH_FAILED"},
        "fraud_flagged": False,
        "risk_score": 0.15,
        "created_at": now - timedelta(days=3),
    },
    # S-10: Large transaction with pending approval refund
    {
        "id": det_uuid(210),
        "user_id": det_uuid(10),
        "amount_paise": 2000000,
        "status": "failed",
        "failure_reason": "MERCHANT_SETTLEMENT_ERROR",
        "merchant_name": "Apple Store Mumbai",
        "payment_method": "credit_card",
        "gateway_response": {"code": "FAILED"},
        "fraud_flagged": False,
        "risk_score": 0.04,
        "created_at": now - timedelta(days=1),
    },
]

SEED_PAYMENTS = [
    {
        "id": det_uuid(301),
        "txn_id": det_uuid(201),
        "gateway": "razorpay",
        "gateway_payment_id": "pay_K5x89Qwer123",
        "payment_method": "upi",
        "amount_paise": 500000,
        "status": "failed",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment was declined by the bank due to insufficient funds.",
        "created_at": now - timedelta(hours=2),
    },
    {
        "id": det_uuid(302),
        "txn_id": det_uuid(202),
        "gateway": "razorpay",
        "gateway_payment_id": "pay_Block987654",
        "payment_method": "credit_card",
        "amount_paise": 2500000,
        "status": "failed",
        "error_code": "GATEWAY_RISK_BLOCK",
        "error_description": "Transaction halted by automated risk filter.",
        "created_at": now - timedelta(hours=5),
    },
    {
        "id": det_uuid(303),
        "txn_id": det_uuid(203),
        "gateway": "razorpay",
        "gateway_payment_id": "pay_SwiggySuccess1",
        "payment_method": "upi",
        "amount_paise": 120000,
        "status": "refunded",
        "error_code": None,
        "error_description": None,
        "created_at": now - timedelta(days=1),
    },
]

SEED_REFUNDS = [
    # S-03: Completed refund for ₹1,200
    {
        "id": det_uuid(401),
        "txn_id": det_uuid(203),
        "amount_paise": 120000,
        "status": "completed",
        "reason": "Order cancelled by merchant",
        "approved_by": None,
        "idempotency_key": "ref_idem_003",
        "created_at": now - timedelta(hours=18),
    },
    # S-10: Large refund pending approval (> ₹10,000)
    {
        "id": det_uuid(402),
        "txn_id": det_uuid(210),
        "amount_paise": 2000000,
        "status": "pending_approval",
        "reason": "Double debit on cancelled order",
        "approved_by": None,
        "idempotency_key": "ref_idem_010",
        "created_at": now - timedelta(hours=12),
    },
]

SEED_TICKETS = [
    # S-09: Open ticket
    {
        "id": det_uuid(501),
        "user_id": det_uuid(9),
        "category": "DISPUTED_CHARGE",
        "description": "Charged twice at supermarket on 2026-09-20. Requesting investigation.",
        "priority": "medium",
        "status": "open",
        "external_ticket_id": "FD-89421",
        "created_at": now - timedelta(hours=6),
    }
]


async def seed_database(session: AsyncSession) -> None:
    """Populate database tables with seed data if not already populated."""
    result = await session.execute(select(User).limit(1))
    if result.scalars().first() is not None:
        print("[seed] Database already contains data. Skipping.")
        return

    print("[seed] Inserting seed users...")
    for u in SEED_USERS:
        session.add(User(**u))
    await session.flush()

    print("[seed] Inserting seed accounts...")
    for a in SEED_ACCOUNTS:
        session.add(Account(**a))
    await session.flush()

    print("[seed] Inserting seed transactions...")
    for t in SEED_TRANSACTIONS:
        session.add(Transaction(**t))
    await session.flush()

    print("[seed] Inserting seed payments...")
    for p in SEED_PAYMENTS:
        session.add(Payment(**p))
    await session.flush()

    print("[seed] Inserting seed refunds...")
    for r in SEED_REFUNDS:
        session.add(Refund(**r))
    await session.flush()

    print("[seed] Inserting seed tickets...")
    for tk in SEED_TICKETS:
        session.add(SupportTicket(**tk))
    await session.flush()

    await session.commit()
    print("[seed] Database seed completed successfully!")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await seed_database(session)


if __name__ == "__main__":
    asyncio.run(main())
