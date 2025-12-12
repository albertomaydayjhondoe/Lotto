"""
Test database utilities
Provides isolated in-memory database for testing
"""
import os
from uuid import uuid4 as _uuid4, UUID as _UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

# Import Base and models
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import Base
from app.models import database  # Import all models to register them


# GUID type for SQLite (stores as string)
class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses PostgreSQL's UUID type, otherwise uses CHAR(36)."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, _UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, _UUID):
                return _UUID(value)
            return value


# Monkey-patch the UUID type to use GUID for SQLite
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import sqlalchemy.dialects.sqlite.base as sqlite_base

# Add visit_UUID method to SQLite compiler
original_visit_uuid = sqlite_base.SQLiteTypeCompiler.visit_uuid if hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_uuid') else None

def visit_UUID(self, type_, **kw):
    return "CHAR(36)"

sqlite_base.SQLiteTypeCompiler.visit_UUID = visit_UUID


# In-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_test_db():
    """Initialize test database by creating all tables"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_test_db():
    """Drop all tables from test database"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_test_session():
    """
    Get a test database session
    This function is used to override the get_db dependency in FastAPI
    """
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
