"""
Test configuration and fixtures for alerting tests.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Monkey-patch SQLite to support UUID type (PostgreSQL UUID renders as CHAR(36) in SQLite)
import sqlalchemy.dialects.sqlite.base as sqlite_base

def visit_UUID(self, type_, **kw):
    """Make UUID compatible with SQLite by rendering as CHAR(36)"""
    return "CHAR(36)"

sqlite_base.SQLiteTypeCompiler.visit_UUID = visit_UUID

from app.models.database import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Create async database session for tests."""
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_db_session(db_session):
    """Alias for db_session for compatibility with different test files."""
    return db_session
