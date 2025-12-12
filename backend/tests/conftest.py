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

# Import ALL models explicitly to ensure they are registered with Base.metadata
# This is required for Base.metadata.create_all() to create all tables
from app.models.database import (
    Base,
    # Core models
    VideoAsset,
    Clip,
    ClipVariant,
    Job,
    Publication,
    Campaign,
    PlatformRule,
    RuleEngineWeights,
    BestClipDecisionModel,
    # Social/Publishing models
    SocialAccountModel,
    PublishLogModel,
    # Alert models
    AlertEventModel,
    # Auth models
    UserModel,
    RefreshTokenModel,
    # AI models
    AIReasoningHistoryModel,
    # Meta Ads models (PASO 10.1)
    MetaAccountModel,
    MetaPixelModel,
    MetaCreativeModel,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaAdInsightsModel,
    MetaAbTestModel,
)

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


# HTTP Test Client Fixtures
@pytest_asyncio.fixture
async def client():
    """Create HTTP test client."""
    from httpx import AsyncClient
    from fastapi import FastAPI
    
    # Create a minimal app with just the meta insights router for testing
    app = FastAPI()
    
    # Mock auth dependencies for testing  
    def mock_auth():
        return {"user_id": "test_user", "roles": ["admin", "manager", "analytics:read"], "sub": "test_user"}
    
    # Import and add the meta insights router
    from app.meta_insights_collector.router import router as meta_insights_router
    from app.auth.permissions import require_role
    
    # Override all possible auth dependencies for tests
    # This is a bit of a hack but works for testing
    for roles in [["admin"], ["manager"], ["user"], ["analytics:read"], ["analytics:read", "manager", "admin"]]:
        app.dependency_overrides[require_role(roles)] = mock_auth
    
    app.include_router(meta_insights_router, tags=["meta-insights"])
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_headers():
    """Create admin headers for testing."""
    # Mock JWT token for admin role
    return {
        "Authorization": "Bearer admin_test_token",
        "Content-Type": "application/json"
    }


@pytest_asyncio.fixture 
async def user_headers():
    """Create user headers for testing."""
    # Mock JWT token for user role
    return {
        "Authorization": "Bearer user_test_token",
        "Content-Type": "application/json"
    }
