"""
Tests for Meta Ads Orchestrator

Tests the complete orchestration flow including:
- Campaign structure creation
- Database persistence
- Insights synchronization
- Error handling
- Action queue processing
"""

import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4, UUID

from app.meta_ads_orchestrator import MetaAdsOrchestrator
from app.meta_ads_orchestrator.models import OrchestrationRequest
from app.models.database import (
    Clip,
    VideoAsset,
    Job,
    SocialAccountModel,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaCreativeModel,
    MetaAdInsightsModel,
)
from sqlalchemy import select


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_clip(async_engine, db_session):
    """Create a test clip for orchestration."""
    # Create video asset first
    video = VideoAsset(
        id=uuid4(),
        title="Test Video",
        description="Test video for orchestration",
        file_path="/test/path.mp4",
        file_size=1024000,
        duration_ms=30000,
    )
    db_session.add(video)
    await db_session.flush()
    
    # Create job
    job = Job(
        id=uuid4(),
        video_asset_id=video.id,
        job_type="clipping",
        status=JobStatus.COMPLETED,
        params={"test": True},
    )
    db_session.add(job)
    await db_session.flush()
    
    # Create clip
    clip = Clip(
        id=uuid4(),
        video_asset_id=video.id,
        start_ms=0,
        end_ms=30000,
        duration_ms=30000,
        status=ClipStatus.COMPLETED,
        visual_score=95.0,
    )
    db_session.add(clip)
    
    await db_session.commit()
    await db_session.refresh(clip)
    
    return clip


@pytest_asyncio.fixture
async def test_social_account(async_engine, db_session):
    """Create a test social account."""
    account = SocialAccountModel(
        id=uuid4(),
        platform="facebook",
        handle="@test_meta_account",
        external_id="123456789",
        is_active=1,
        oauth_access_token="test_token_stub_mode",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    
    return account


# ============================================================================
# Orchestration Flow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrate_campaign_full_flow(db_session, test_clip, test_social_account):
    """Test complete orchestration flow: campaign → adset → ad → creative → insights."""
    orchestrator = MetaAdsOrchestrator(db_session)
    
    request = OrchestrationRequest(
        social_account_id=test_social_account.id,
        clip_id=test_clip.id,
        campaign_name="Black Friday 2025",
        campaign_objective="OUTCOME_SALES",
        daily_budget_cents=50000,  # $500
        optimization_goal="LINK_CLICKS",
        creative_title="Amazing Product Launch",
        creative_description="Don't miss this incredible deal!",
        landing_url="https://example.com/product",
        auto_publish=False,
    )
    
    result = await orchestrator.orchestrate_campaign(request)
    
    # Verify overall success
    assert result.overall_success is True
    assert result.errors == []
    assert result.campaign_creation is not None
    assert result.campaign_creation.success is True
    
    # Verify all IDs are present
    assert result.campaign_creation.campaign_db_id > 0
    assert result.campaign_creation.campaign_meta_id.startswith("META_CAMPAIGN_")
    assert result.campaign_creation.adset_db_id > 0
    assert result.campaign_creation.adset_meta_id.startswith("META_ADSET_")
    assert result.campaign_creation.ad_db_id > 0
    assert result.campaign_creation.ad_meta_id.startswith("META_AD_")
    assert result.campaign_creation.creative_db_id > 0
    assert result.campaign_creation.creative_meta_id.startswith("META_CREATIVE_")
    
    # Verify insights were synced
    assert result.insights_sync is not None
    assert result.insights_sync.success is True
    assert result.insights_sync.insights_synced >= 1
    
    # Verify duration was calculated
    assert result.duration_seconds is not None
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_orchestrate_campaign_persists_to_database(db_session, test_clip, test_social_account):
    """Test that orchestration persists all entities to database."""
    orchestrator = MetaAdsOrchestrator(db_session)
    
    request = OrchestrationRequest(
        social_account_id=test_social_account.id,
        clip_id=test_clip.id,
        campaign_name="Database Persistence Test",
        campaign_objective="OUTCOME_TRAFFIC",
        daily_budget_cents=10000,
        creative_title="Test Title",
        creative_description="Test Description",
        landing_url="https://example.com",
    )
    
    result = await orchestrator.orchestrate_campaign(request)
    
    assert result.overall_success is True
    
    # Verify campaign in DB
    campaign_result = await db_session.execute(
        select(MetaCampaignModel).where(
            MetaCampaignModel.id == result.campaign_creation.campaign_db_id
        )
    )
    campaign = campaign_result.scalar_one()
    assert campaign.name == "Database Persistence Test"
    assert campaign.objective == "OUTCOME_TRAFFIC"
    assert campaign.daily_budget == 10000
    assert campaign.status == "PAUSED"  # auto_publish=False
    
    # Verify adset in DB
    adset_result = await db_session.execute(
        select(MetaAdsetModel).where(
            MetaAdsetModel.id == result.campaign_creation.adset_db_id
        )
    )
    adset = adset_result.scalar_one()
    assert adset.campaign_id == campaign.id
    assert adset.optimization_goal == "LINK_CLICKS"
    
    # Verify ad in DB
    ad_result = await db_session.execute(
        select(MetaAdModel).where(
            MetaAdModel.id == result.campaign_creation.ad_db_id
        )
    )
    ad = ad_result.scalar_one()
    assert ad.adset_id == adset.id
    
    # Verify creative in DB
    creative_result = await db_session.execute(
        select(MetaCreativeModel).where(
            MetaCreativeModel.id == result.campaign_creation.creative_db_id
        )
    )
    creative = creative_result.scalar_one()
    assert creative.name is not None


@pytest.mark.asyncio
async def test_orchestrate_campaign_with_auto_publish(db_session, test_clip, test_social_account):
    """Test orchestration with auto_publish=True creates ACTIVE entities."""
    orchestrator = MetaAdsOrchestrator(db_session)
    
    request = OrchestrationRequest(
        social_account_id=test_social_account.id,
        clip_id=test_clip.id,
        campaign_name="Auto Publish Test",
        campaign_objective="OUTCOME_ENGAGEMENT",
        daily_budget_cents=20000,
        creative_title="Auto Published Ad",
        creative_description="This should be active",
        landing_url="https://example.com",
        auto_publish=True,  # Should create ACTIVE status
    )
    
    result = await orchestrator.orchestrate_campaign(request)
    
    assert result.overall_success is True
    
    # Verify campaign is ACTIVE
    campaign_result = await db_session.execute(
        select(MetaCampaignModel).where(
            MetaCampaignModel.id == result.campaign_creation.campaign_db_id
        )
    )
    campaign = campaign_result.scalar_one()
    assert campaign.status == "ACTIVE"


@pytest.mark.asyncio
async def test_orchestrate_campaign_invalid_clip_fails(db_session, test_social_account):
    """Test that orchestration fails gracefully with invalid clip ID."""
    orchestrator = MetaAdsOrchestrator(db_session)
    
    fake_clip_id = uuid4()
    
    request = OrchestrationRequest(
        social_account_id=test_social_account.id,
        clip_id=fake_clip_id,
        campaign_name="Should Fail",
        campaign_objective="OUTCOME_SALES",
        daily_budget_cents=10000,
        creative_title="Test",
        creative_description="Test",
        landing_url="https://example.com",
    )
    
    result = await orchestrator.orchestrate_campaign(request)
    
    # Should fail overall
    assert result.overall_success is False
    assert len(result.errors) > 0
    assert "not found" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_orchestration_respects_budget(db_session, test_clip, test_social_account):
    """Test that budget parameters are correctly set."""
    orchestrator = MetaAdsOrchestrator(db_session)
    
    budget_cents = 75000  # $750
    
    request = OrchestrationRequest(
        social_account_id=test_social_account.id,
        clip_id=test_clip.id,
        campaign_name="Budget Test",
        campaign_objective="OUTCOME_TRAFFIC",
        daily_budget_cents=budget_cents,
        creative_title="Test",
        creative_description="Test",
        landing_url="https://example.com",
    )
    
    result = await orchestrator.orchestrate_campaign(request)
    
    assert result.overall_success is True
    
    # Verify campaign budget
    campaign = await db_session.get(MetaCampaignModel, result.campaign_creation.campaign_db_id)
    assert campaign.daily_budget == budget_cents
    
    # Verify adset budget matches
    adset = await db_session.get(MetaAdsetModel, result.campaign_creation.adset_db_id)
    assert adset.daily_budget == budget_cents
