"""
Tests for Publishing Engine models - Social Accounts and Publish Logs
"""
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    SocialAccountModel,
    PublishLogModel,
    Clip,
    VideoAsset,
    ClipStatus
)
from tests.test_db import init_test_db, drop_test_db, get_test_session


# Test fixtures
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Initialize test database before each test."""
    await init_test_db()
    yield
    await drop_test_db()


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for tests"""
    async for session in get_test_session():
        yield session


@pytest_asyncio.fixture
async def test_clip(db_session):
    """Create a test clip for publish log tests."""
    # Create video asset first
    video_asset = VideoAsset(
        id=uuid4(),
        title="Test Video",
        file_path="/storage/test.mp4",
        file_size=1000000,
        duration_ms=30000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(video_asset)
    await db_session.flush()
    
    # Create clip
    clip = Clip(
        id=uuid4(),
        video_asset_id=video_asset.id,
        start_ms=1000,
        end_ms=11000,
        duration_ms=10000,
        visual_score=0.85,
        status=ClipStatus.READY,
        params={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(clip)
    await db_session.commit()
    
    return clip


@pytest.mark.asyncio
async def test_create_social_account_ok(db_session):
    """Test creating a social account with main account flag."""
    # Create social account
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo_oficial",
        is_main_account=1,  # True (SQLite-compatible integer)
        is_active=1,  # True
        extra_metadata={"followers": 1000, "verified": True}
    )
    
    db_session.add(account)
    await db_session.commit()
    
    # Query back
    stmt = select(SocialAccountModel).where(SocialAccountModel.handle == "@stakazo_oficial")
    result = await db_session.execute(stmt)
    retrieved_account = result.scalar_one()
    
    # Assertions
    assert retrieved_account is not None
    assert retrieved_account.platform == "instagram"
    assert retrieved_account.handle == "@stakazo_oficial"
    assert retrieved_account.is_main_account == 1
    assert retrieved_account.is_active == 1  # Default is True (1)
    assert retrieved_account.extra_metadata["followers"] == 1000
    assert retrieved_account.created_at is not None
    assert retrieved_account.updated_at is not None


@pytest.mark.asyncio
async def test_create_publish_log_for_clip(db_session, test_clip):
    """Test creating a publish log linked to a clip and social account."""
    # Create social account
    account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo_test",
        is_main_account=0,  # False
        is_active=1
    )
    db_session.add(account)
    await db_session.flush()
    
    # Create publish log
    publish_log = PublishLogModel(
        id=uuid4(),
        clip_id=test_clip.id,
        platform="instagram",
        social_account_id=account.id,
        status="pending",
        extra_metadata={"caption": "Test post", "hashtags": ["#test"]}
    )
    
    db_session.add(publish_log)
    await db_session.commit()
    
    # Query back with relationships
    stmt = select(PublishLogModel).where(PublishLogModel.id == publish_log.id)
    result = await db_session.execute(stmt)
    retrieved_log = result.scalar_one()
    
    # Assertions
    assert retrieved_log is not None
    assert retrieved_log.clip_id == test_clip.id
    assert retrieved_log.platform == "instagram"
    assert retrieved_log.status == "pending"
    assert retrieved_log.social_account_id == account.id
    
    # Test relationships
    assert retrieved_log.clip is not None
    assert retrieved_log.clip.id == test_clip.id
    
    assert retrieved_log.social_account is not None
    assert retrieved_log.social_account.handle == "@stakazo_test"
    
    # Test extra_metadata
    assert retrieved_log.extra_metadata["caption"] == "Test post"
    assert "hashtags" in retrieved_log.extra_metadata


@pytest.mark.asyncio
async def test_publish_log_indexes(db_session, test_clip):
    """Test that publish log queries work correctly (implicitly testing indexes)."""
    # Create multiple social accounts
    account1 = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@account1",
        is_active=1
    )
    account2 = SocialAccountModel(
        id=uuid4(),
        platform="tiktok",
        handle="@account2",
        is_active=1
    )
    db_session.add_all([account1, account2])
    await db_session.flush()
    
    # Create multiple publish logs with different statuses and platforms
    logs = [
        PublishLogModel(
            id=uuid4(),
            clip_id=test_clip.id,
            platform="instagram",
            social_account_id=account1.id,
            status="pending"
        ),
        PublishLogModel(
            id=uuid4(),
            clip_id=test_clip.id,
            platform="instagram",
            social_account_id=account1.id,
            status="success",
            external_post_id="ig_12345",
            external_url="https://instagram.com/p/12345",
            published_at=datetime.utcnow()
        ),
        PublishLogModel(
            id=uuid4(),
            clip_id=test_clip.id,
            platform="tiktok",
            social_account_id=account2.id,
            status="pending"
        ),
        PublishLogModel(
            id=uuid4(),
            clip_id=test_clip.id,
            platform="instagram",
            social_account_id=account1.id,
            status="failed",
            error_message="API rate limit exceeded"
        ),
    ]
    
    db_session.add_all(logs)
    await db_session.commit()
    
    # Query by platform and status (tests compound index)
    stmt = select(PublishLogModel).where(
        PublishLogModel.platform == "instagram",
        PublishLogModel.status == "pending"
    )
    result = await db_session.execute(stmt)
    pending_instagram = result.scalars().all()
    
    assert len(pending_instagram) == 1
    assert pending_instagram[0].platform == "instagram"
    assert pending_instagram[0].status == "pending"
    
    # Query by clip_id (tests clip_id index)
    stmt = select(PublishLogModel).where(PublishLogModel.clip_id == test_clip.id)
    result = await db_session.execute(stmt)
    all_logs_for_clip = result.scalars().all()
    
    assert len(all_logs_for_clip) == 4
    
    # Query by social_account_id (tests social_account_id index)
    stmt = select(PublishLogModel).where(PublishLogModel.social_account_id == account1.id)
    result = await db_session.execute(stmt)
    account1_logs = result.scalars().all()
    
    assert len(account1_logs) == 3  # account1 has 3 logs
    
    # Verify failed log has error message
    failed_logs = [log for log in all_logs_for_clip if log.status == "failed"]
    assert len(failed_logs) == 1
    assert failed_logs[0].error_message == "API rate limit exceeded"
    
    # Verify success log has external data
    success_logs = [log for log in all_logs_for_clip if log.status == "success"]
    assert len(success_logs) == 1
    assert success_logs[0].external_post_id == "ig_12345"
    assert success_logs[0].external_url == "https://instagram.com/p/12345"
    assert success_logs[0].published_at is not None


@pytest.mark.asyncio
async def test_multiple_accounts_same_platform(db_session):
    """Test creating multiple accounts for the same platform (main + satellites)."""
    # Create main account
    main_account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo_oficial",
        is_main_account=1,
        is_active=1
    )
    
    # Create satellite accounts
    satellite1 = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo_gaming",
        is_main_account=0,
        is_active=1
    )
    
    satellite2 = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@stakazo_news",
        is_main_account=0,
        is_active=0  # Inactive
    )
    
    db_session.add_all([main_account, satellite1, satellite2])
    await db_session.commit()
    
    # Query active Instagram accounts
    stmt = select(SocialAccountModel).where(
        SocialAccountModel.platform == "instagram",
        SocialAccountModel.is_active == 1
    )
    result = await db_session.execute(stmt)
    active_accounts = result.scalars().all()
    
    assert len(active_accounts) == 2
    
    # Query main account
    stmt = select(SocialAccountModel).where(
        SocialAccountModel.platform == "instagram",
        SocialAccountModel.is_main_account == 1
    )
    result = await db_session.execute(stmt)
    main = result.scalar_one()
    
    assert main.handle == "@stakazo_oficial"


@pytest.mark.asyncio
async def test_publish_log_without_social_account(db_session, test_clip):
    """Test creating a publish log without linking to a specific social account."""
    # Create publish log without social_account_id (auto-publish scenario)
    publish_log = PublishLogModel(
        id=uuid4(),
        clip_id=test_clip.id,
        platform="youtube",
        social_account_id=None,  # No specific account
        status="pending",
        extra_metadata={"auto_publish": True}
    )
    
    db_session.add(publish_log)
    await db_session.commit()
    
    # Query back
    stmt = select(PublishLogModel).where(PublishLogModel.id == publish_log.id)
    result = await db_session.execute(stmt)
    retrieved_log = result.scalar_one()
    
    # Assertions
    assert retrieved_log.social_account_id is None
    assert retrieved_log.social_account is None
    assert retrieved_log.clip is not None
    assert retrieved_log.extra_metadata["auto_publish"] is True
