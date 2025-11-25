"""
Simple tests for Meta Ads models to verify basic functionality
"""
import pytest
from datetime import datetime
from app.models.database import (
    SocialAccountModel,
    VideoAsset,
    MetaAccountModel,
    MetaPixelModel,
    MetaCreativeModel,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaAdInsightsModel,
)


@pytest.mark.asyncio
async def test_create_meta_account(db_session):
    """Test creating a Meta account"""
    # Create social account first
    social = SocialAccountModel(
        user_id="test_user",
        platform_type="instagram",
        username="test_account",
        platform_account_id="insta_123",
        account_name="Test Account",
        access_token="token",
        is_active=1,
    )
    db_session.add(social)
    await db_session.commit()
    await db_session.refresh(social)
    
    # Create Meta account
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_123",
        account_name="Test Meta Account",
        currency="USD",
    )
    db_session.add(meta)
    await db_session.commit()
    await db_session.refresh(meta)
    
    assert meta.id is not None
    assert meta.ad_account_id == "act_123"
    assert meta.social_account_id == social.id


@pytest.mark.asyncio
async def test_create_meta_campaign(db_session):
    """Test creating a Meta campaign"""
    # Setup
    social = SocialAccountModel(
        user_id="test_user",
        platform_type="instagram",
        username="test",
        platform_account_id="insta_123",
        account_name="Test",
        access_token="token",
        is_active=1,
    )
    db_session.add(social)
    await db_session.commit()
    await db_session.refresh(social)
    
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_123",
        account_name="Test Meta",
        currency="USD",
    )
    db_session.add(meta)
    await db_session.commit()
    await db_session.refresh(meta)
    
    # Create campaign
    campaign = MetaCampaignModel(
        meta_account_id=meta.id,
        campaign_id="camp_123",
        campaign_name="Test Campaign",
        objective="CONVERSIONS",
        status="PAUSED",
        daily_budget=100.0,
        utm_source="facebook",
        utm_medium="paid",
        requires_approval=1,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    
    assert campaign.id is not None
    assert campaign.campaign_name == "Test Campaign"
    assert campaign.requires_approval == 1
    assert campaign.is_approved == 0


@pytest.mark.asyncio
async def test_meta_creative_with_video(db_session):
    """Test creating a Meta creative linked to a video asset"""
    # Create video asset
    video = VideoAsset(
        filename="test.mp4",
        original_path="/uploads/test.mp4",
        file_size=1024000,
        duration_seconds=60.0,
        format="mp4",
        status="ready",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    
    # Create creative
    creative = MetaCreativeModel(
        video_asset_id=video.id,
        creative_id="cre_123",
        creative_name="Test Creative",
        creative_type="video",
        video_url="https://example.com/video.mp4",
        duration_ms=60000,
        genre="comedy",
        is_approved=1,
    )
    db_session.add(creative)
    await db_session.commit()
    await db_session.refresh(creative)
    
    assert creative.id is not None
    assert creative.video_asset_id == video.id
    assert creative.is_approved == 1
    assert creative.genre == "comedy"


@pytest.mark.asyncio
async def test_campaign_hierarchy(db_session):
    """Test the full campaign → adset → ad hierarchy"""
    # Setup social and meta account
    social = SocialAccountModel(
        user_id="test_user",
        platform_type="instagram",
        username="test",
        platform_account_id="insta_123",
        account_name="Test",
        access_token="token",
        is_active=1,
    )
    db_session.add(social)
    await db_session.commit()
    await db_session.refresh(social)
    
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_123",
        account_name="Test Meta",
        currency="USD",
    )
    db_session.add(meta)
    await db_session.commit()
    await db_session.refresh(meta)
    
    # Create campaign
    campaign = MetaCampaignModel(
        meta_account_id=meta.id,
        campaign_id="camp_123",
        campaign_name="Test Campaign",
        objective="CONVERSIONS",
        status="ACTIVE",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    
    # Create adset
    adset = MetaAdsetModel(
        campaign_id=campaign.id,
        adset_id="adset_123",
        adset_name="Test Adset",
        status="ACTIVE",
        daily_budget=50.0,
    )
    db_session.add(adset)
    await db_session.commit()
    await db_session.refresh(adset)
    
    # Create ad
    ad = MetaAdModel(
        adset_id=adset.id,
        ad_id="ad_123",
        ad_name="Test Ad",
        status="ACTIVE",
        headline="Test Headline",
    )
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)
    
    # Create insights
    insights = MetaAdInsightsModel(
        ad_id=ad.id,
        date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        impressions=1000,
        reach=800,
        clicks=50,
        spend=25.0,
    )
    db_session.add(insights)
    await db_session.commit()
    await db_session.refresh(insights)
    
    # Verify hierarchy
    assert campaign.id is not None
    assert adset.campaign_id == campaign.id
    assert ad.adset_id == adset.id
    assert insights.ad_id == ad.id


@pytest.mark.asyncio
async def test_meta_pixel(db_session):
    """Test creating a Meta pixel"""
    # Setup
    social = SocialAccountModel(
        user_id="test_user",
        platform_type="instagram",
        username="test",
        platform_account_id="insta_123",
        account_name="Test",
        access_token="token",
        is_active=1,
    )
    db_session.add(social)
    await db_session.commit()
    await db_session.refresh(social)
    
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_123",
        account_name="Test Meta",
        currency="USD",
    )
    db_session.add(meta)
    await db_session.commit()
    await db_session.refresh(meta)
    
    # Create pixel
    pixel = MetaPixelModel(
        meta_account_id=meta.id,
        pixel_id="pix_123",
        pixel_name="Test Pixel",
        is_active=1,
    )
    db_session.add(pixel)
    await db_session.commit()
    await db_session.refresh(pixel)
    
    assert pixel.id is not None
    assert pixel.pixel_id == "pix_123"
    assert pixel.is_active == 1
    assert pixel.meta_account_id == meta.id
