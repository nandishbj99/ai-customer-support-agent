import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.seeds.seed_data import seed_database


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite async database pre-populated with seed data for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await seed_database(session)

    async with session_maker() as session:
        yield session

    await engine.dispose()
