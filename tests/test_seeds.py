import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.models import Account, Payment, Refund, SupportTicket, Transaction, User
from app.seeds.seed_data import det_uuid, seed_database


@pytest.mark.asyncio
async def test_seed_database_execution():
    """Verify that seed_database populates all tables with realistic scenarios."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await seed_database(session)

        # Assert users
        users = (await session.execute(select(User))).scalars().all()
        assert len(users) >= 15

        # Assert accounts
        accounts = (await session.execute(select(Account))).scalars().all()
        assert len(accounts) >= 15

        # Assert S-01 (insufficient funds scenario)
        u1_account = (
            await session.execute(select(Account).where(Account.user_id == det_uuid(1)))
        ).scalars().first()
        assert u1_account is not None
        assert u1_account.balance_paise == 320000  # ₹3,200

        u1_txn = (
            await session.execute(select(Transaction).where(Transaction.user_id == det_uuid(1)))
        ).scalars().first()
        assert u1_txn is not None
        assert u1_txn.amount_paise == 500000  # ₹5,000 > ₹3,200
        assert u1_txn.status == "failed"
        assert u1_txn.failure_reason == "INSUFFICIENT_FUNDS"

        # Assert S-02 (fraud risk scenario)
        u2_txn = (
            await session.execute(select(Transaction).where(Transaction.user_id == det_uuid(2)))
        ).scalars().first()
        assert u2_txn is not None
        assert u2_txn.fraud_flagged is True
        assert float(u2_txn.risk_score) >= 0.8

        # Assert S-05 (frozen account scenario)
        u5_account = (
            await session.execute(select(Account).where(Account.user_id == det_uuid(5)))
        ).scalars().first()
        assert u5_account is not None
        assert u5_account.status == "frozen"

        # Assert S-04 (large transaction > ₹10K HITL threshold)
        u4_txn = (
            await session.execute(select(Transaction).where(Transaction.user_id == det_uuid(4)))
        ).scalars().first()
        assert u4_txn is not None
        assert u4_txn.amount_paise == 1500000  # ₹15,000

    await test_engine.dispose()
