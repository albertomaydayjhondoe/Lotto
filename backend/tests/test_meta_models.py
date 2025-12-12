"""
Tests for Meta Ads Models - PASO 10.1

Tests the complete Meta Ads database schema:
- MetaAccountModel
- MetaPixelModel
- MetaCreativeModel
- MetaCampaignModel
- MetaAdsetModel
- MetaAdModel
- MetaAdInsightsModel

Validates:
- Model creation
- Relationships (1:1, 1:N, cascade)
- Index performance
- SQLite + PostgreSQL compatibility
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.database import (
    VideoAsset,
    SocialAccountModel,
    MetaAccountModel,
    MetaPixelModel,
    MetaCreativeModel,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
    MetaAdInsightsModel,
)


@pytest.fixture
def social_account(db_session: Session):
    """Create a test social account."""
    account = SocialAccountModel(
        platform="facebook",
        handle="@testaccount",
        external_id="fb_123456",
        is_main_account=1,
        is_active=1,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def video_asset(db_session: Session):
    """Create a test video asset."""
    asset = VideoAsset(
        title="Test Video",
        description="Test video for Meta Ads",
        duration_ms=30000,
        file_path="/videos/test.mp4",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


@pytest.fixture
def meta_account(db_session: Session, social_account: SocialAccountModel):
    """Create a test Meta account."""
    account = MetaAccountModel(
        social_account_id=social_account.id,
        ad_account_id="act_123456789",
        business_id="biz_987654321",
        account_name="Test Ad Account",
        currency="USD",
        timezone="America/Los_Angeles",
        is_active=1,
        account_status="ACTIVE",
        spend_cap=10000.0,
        amount_spent=0.0,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


class TestMetaModelsCreation:
    """Test creating Meta Ads models."""
    
    def test_create_meta_account(self, db_session: Session, social_account: SocialAccountModel):
        """Test creating a Meta account."""
        account = MetaAccountModel(
            social_account_id=social_account.id,
            ad_account_id="act_111222333",
            business_id="biz_444555666",
            account_name="New Test Account",
            currency="EUR",
            timezone="Europe/London",
            is_active=1,
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        assert account.id is not None
        assert account.ad_account_id == "act_111222333"
        assert account.currency == "EUR"
        assert account.is_active == 1
        assert account.created_at is not None
    
    def test_create_meta_pixel(self, db_session: Session, meta_account: MetaAccountModel):
        """Test creating a Meta pixel."""
        pixel = MetaPixelModel(
            meta_account_id=meta_account.id,
            pixel_id="pix_123456",
            pixel_name="Test Pixel",
            is_active=1,
        )
        db_session.add(pixel)
        db_session.commit()
        db_session.refresh(pixel)
        
        assert pixel.id is not None
        assert pixel.pixel_id == "pix_123456"
        assert pixel.pixel_name == "Test Pixel"
        assert pixel.is_active == 1
    
    def test_create_meta_creative(self, db_session: Session, video_asset: VideoAsset):
        """Test creating a Meta creative."""
        creative = MetaCreativeModel(
            video_asset_id=video_asset.id,
            creative_id="cre_789012",
            creative_name="Test Creative",
            creative_type="video",
            video_url="https://facebook.com/videos/123.mp4",
            thumbnail_url="https://facebook.com/thumbs/123.jpg",
            duration_ms=30000,
            status="active",
            is_approved=0,
            is_reviewed=0,
            genre="entertainment",
            subgenre="comedy",
            age_restriction="13+",
        )
        db_session.add(creative)
        db_session.commit()
        db_session.refresh(creative)
        
        assert creative.id is not None
        assert creative.creative_id == "cre_789012"
        assert creative.creative_type == "video"
        assert creative.genre == "entertainment"
        assert creative.is_approved == 0
    
    def test_create_meta_campaign(self, db_session: Session, meta_account: MetaAccountModel):
        """Test creating a Meta campaign."""
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_345678",
            campaign_name="Test Campaign",
            objective="VIDEO_VIEWS",
            status="PAUSED",
            daily_budget=100.0,
            lifetime_budget=3000.0,
            requires_approval=1,
            is_approved=0,
            utm_source="facebook",
            utm_medium="paid",
            utm_campaign="test_campaign",
        )
        db_session.add(campaign)
        db_session.commit()
        db_session.refresh(campaign)
        
        assert campaign.id is not None
        assert campaign.campaign_name == "Test Campaign"
        assert campaign.objective == "VIDEO_VIEWS"
        assert campaign.daily_budget == 100.0
        assert campaign.requires_approval == 1
    
    def test_create_meta_adset(self, db_session: Session, meta_account: MetaAccountModel):
        """Test creating a Meta adset."""
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_111",
            campaign_name="Parent Campaign",
            objective="REACH",
            status="PAUSED",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_222",
            adset_name="Test Adset",
            status="PAUSED",
            daily_budget=50.0,
            bid_amount=0.50,
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            targeting={"interests": ["technology", "gaming"]},
            age_min=18,
            age_max=65,
            gender="all",
            locations=["US", "CA", "UK"],
            optimization_goal="IMPRESSIONS",
        )
        db_session.add(adset)
        db_session.commit()
        db_session.refresh(adset)
        
        assert adset.id is not None
        assert adset.adset_name == "Test Adset"
        assert adset.age_min == 18
        assert adset.age_max == 65
        assert adset.gender == "all"
    
    def test_create_meta_ad(self, db_session: Session, meta_account: MetaAccountModel, video_asset: VideoAsset):
        """Test creating a Meta ad."""
        # Create hierarchy
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_333",
            campaign_name="Ad Campaign",
            objective="VIDEO_VIEWS",
            status="PAUSED",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_444",
            adset_name="Ad Adset",
            status="PAUSED",
        )
        db_session.add(adset)
        db_session.commit()
        
        creative = MetaCreativeModel(
            video_asset_id=video_asset.id,
            creative_id="cre_555",
            creative_name="Ad Creative",
            creative_type="video",
            status="active",
        )
        db_session.add(creative)
        db_session.commit()
        
        ad = MetaAdModel(
            adset_id=adset.id,
            creative_id=creative.id,
            ad_id="ad_666",
            ad_name="Test Ad",
            status="PAUSED",
            headline="Amazing Video",
            primary_text="Check out this awesome video!",
            description="You won't believe what happens next",
            call_to_action="WATCH_MORE",
            link_url="https://example.com/video",
            pixel_id="pix_123456",
            is_reviewed=0,
        )
        db_session.add(ad)
        db_session.commit()
        db_session.refresh(ad)
        
        assert ad.id is not None
        assert ad.ad_name == "Test Ad"
        assert ad.headline == "Amazing Video"
        assert ad.pixel_id == "pix_123456"
    
    def test_create_meta_insights(self, db_session: Session, meta_account: MetaAccountModel):
        """Test creating Meta ad insights."""
        # Create full hierarchy
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_777",
            campaign_name="Insights Campaign",
            objective="VIDEO_VIEWS",
            status="ACTIVE",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_888",
            adset_name="Insights Adset",
            status="ACTIVE",
        )
        db_session.add(adset)
        db_session.commit()
        
        ad = MetaAdModel(
            adset_id=adset.id,
            ad_id="ad_999",
            ad_name="Insights Ad",
            status="ACTIVE",
        )
        db_session.add(ad)
        db_session.commit()
        
        insights = MetaAdInsightsModel(
            ad_id=ad.id,
            date=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            impressions=10000,
            reach=8000,
            frequency=1.25,
            clicks=500,
            inline_link_clicks=450,
            unique_clicks=400,
            ctr=5.0,
            video_views=3000,
            video_views_3s=2500,
            video_views_10s=2000,
            video_views_25_percent=1500,
            video_views_50_percent=1000,
            video_views_75_percent=500,
            video_views_100_percent=200,
            video_avg_watch_time=15.5,
            spend=100.50,
            cpc=0.20,
            cpm=10.05,
            conversions=25,
            conversion_rate=5.0,
            cost_per_conversion=4.02,
            purchase_value=500.0,
            roas=4.98,
        )
        db_session.add(insights)
        db_session.commit()
        db_session.refresh(insights)
        
        assert insights.id is not None
        assert insights.impressions == 10000
        assert insights.reach == 8000
        assert insights.video_views == 3000
        assert insights.spend == 100.50
        assert insights.roas == 4.98


class TestMetaModelsRelations:
    """Test relationships between Meta Ads models."""
    
    def test_social_account_to_meta_account_1to1(self, db_session: Session, social_account: SocialAccountModel, meta_account: MetaAccountModel):
        """Test 1:1 relationship between SocialAccount and MetaAccount."""
        # Query from social account side
        stmt = select(SocialAccountModel).where(SocialAccountModel.id == social_account.id)
        result = db_session.execute(stmt).scalar_one()
        
        assert result.meta_account is not None
        assert result.meta_account.ad_account_id == meta_account.ad_account_id
        
        # Query from meta account side
        stmt = select(MetaAccountModel).where(MetaAccountModel.id == meta_account.id)
        result = db_session.execute(stmt).scalar_one()
        
        assert result.social_account is not None
        assert result.social_account.platform == "facebook"
    
    def test_video_asset_to_creatives_1toN(self, db_session: Session, video_asset: VideoAsset):
        """Test 1:N relationship between VideoAsset and MetaCreative."""
        # Create multiple creatives for same video
        creatives = []
        for i in range(3):
            creative = MetaCreativeModel(
                video_asset_id=video_asset.id,
                creative_id=f"cre_multi_{i}",
                creative_name=f"Creative {i}",
                creative_type="video",
                status="active",
            )
            creatives.append(creative)
            db_session.add(creative)
        
        db_session.commit()
        
        # Query from video asset side
        stmt = select(VideoAsset).where(VideoAsset.id == video_asset.id)
        result = db_session.execute(stmt).scalar_one()
        
        assert len(result.meta_creatives) == 3
        assert all(c.video_asset_id == video_asset.id for c in result.meta_creatives)
    
    def test_campaign_hierarchy(self, db_session: Session, meta_account: MetaAccountModel):
        """Test Campaign → Adset → Ad → Insights hierarchy."""
        # Create campaign
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_hierarchy",
            campaign_name="Hierarchy Test",
            objective="VIDEO_VIEWS",
            status="ACTIVE",
        )
        db_session.add(campaign)
        db_session.commit()
        
        # Create adsets
        adset1 = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_h1",
            adset_name="Adset 1",
            status="ACTIVE",
        )
        adset2 = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_h2",
            adset_name="Adset 2",
            status="PAUSED",
        )
        db_session.add_all([adset1, adset2])
        db_session.commit()
        
        # Create ads
        ad1 = MetaAdModel(
            adset_id=adset1.id,
            ad_id="ad_h1",
            ad_name="Ad 1",
            status="ACTIVE",
        )
        ad2 = MetaAdModel(
            adset_id=adset1.id,
            ad_id="ad_h2",
            ad_name="Ad 2",
            status="ACTIVE",
        )
        db_session.add_all([ad1, ad2])
        db_session.commit()
        
        # Create insights
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        insight1 = MetaAdInsightsModel(
            ad_id=ad1.id,
            date=today,
            impressions=5000,
            clicks=250,
        )
        insight2 = MetaAdInsightsModel(
            ad_id=ad1.id,
            date=today - timedelta(days=1),
            impressions=4000,
            clicks=200,
        )
        db_session.add_all([insight1, insight2])
        db_session.commit()
        
        # Query and verify hierarchy
        stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign.id)
        result = db_session.execute(stmt).scalar_one()
        
        assert len(result.adsets) == 2
        assert len(result.adsets[0].ads) == 2
        assert len(result.adsets[0].ads[0].insights) == 2
    
    def test_cascade_delete_campaign(self, db_session: Session, meta_account: MetaAccountModel):
        """Test cascade delete from campaign down to insights."""
        # Create full hierarchy
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_cascade",
            campaign_name="Cascade Test",
            objective="REACH",
            status="ACTIVE",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_cascade",
            adset_name="Cascade Adset",
            status="ACTIVE",
        )
        db_session.add(adset)
        db_session.commit()
        
        ad = MetaAdModel(
            adset_id=adset.id,
            ad_id="ad_cascade",
            ad_name="Cascade Ad",
            status="ACTIVE",
        )
        db_session.add(ad)
        db_session.commit()
        
        insight = MetaAdInsightsModel(
            ad_id=ad.id,
            date=datetime.utcnow(),
            impressions=1000,
        )
        db_session.add(insight)
        db_session.commit()
        
        # Get IDs before delete
        campaign_id = campaign.id
        adset_id = adset.id
        ad_id = ad.id
        insight_id = insight.id
        
        # Delete campaign
        db_session.delete(campaign)
        db_session.commit()
        
        # Verify cascade delete
        assert db_session.get(MetaCampaignModel, campaign_id) is None
        assert db_session.get(MetaAdsetModel, adset_id) is None
        assert db_session.get(MetaAdModel, ad_id) is None
        assert db_session.get(MetaAdInsightsModel, insight_id) is None


class TestMetaModelsIndexes:
    """Test index performance on Meta Ads models."""
    
    def test_query_by_ad_account_id(self, db_session: Session, meta_account: MetaAccountModel):
        """Test indexed query by ad_account_id."""
        stmt = select(MetaAccountModel).where(MetaAccountModel.ad_account_id == meta_account.ad_account_id)
        result = db_session.execute(stmt).scalar_one()
        
        assert result.id == meta_account.id
    
    def test_query_campaigns_by_status(self, db_session: Session, meta_account: MetaAccountModel):
        """Test indexed query by campaign status."""
        # Create campaigns with different statuses
        for i, status in enumerate(["ACTIVE", "PAUSED", "ACTIVE", "PAUSED", "ACTIVE"]):
            campaign = MetaCampaignModel(
                meta_account_id=meta_account.id,
                campaign_id=f"cam_status_{i}",
                campaign_name=f"Campaign {i}",
                objective="REACH",
                status=status,
            )
            db_session.add(campaign)
        
        db_session.commit()
        
        # Query active campaigns
        stmt = select(func.count()).select_from(MetaCampaignModel).where(MetaCampaignModel.status == "ACTIVE")
        count = db_session.execute(stmt).scalar()
        
        assert count == 3
    
    def test_query_insights_by_date_range(self, db_session: Session, meta_account: MetaAccountModel):
        """Test indexed query by date range."""
        # Create campaign/adset/ad
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_dates",
            campaign_name="Date Test",
            objective="VIDEO_VIEWS",
            status="ACTIVE",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_dates",
            adset_name="Date Adset",
            status="ACTIVE",
        )
        db_session.add(adset)
        db_session.commit()
        
        ad = MetaAdModel(
            adset_id=adset.id,
            ad_id="ad_dates",
            ad_name="Date Ad",
            status="ACTIVE",
        )
        db_session.add(ad)
        db_session.commit()
        
        # Create insights for last 7 days
        base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(7):
            insight = MetaAdInsightsModel(
                ad_id=ad.id,
                date=base_date - timedelta(days=i),
                impressions=1000 * (i + 1),
                spend=10.0 * (i + 1),
            )
            db_session.add(insight)
        
        db_session.commit()
        
        # Query last 3 days
        start_date = base_date - timedelta(days=2)
        stmt = select(MetaAdInsightsModel).where(
            MetaAdInsightsModel.ad_id == ad.id,
            MetaAdInsightsModel.date >= start_date
        ).order_by(MetaAdInsightsModel.date.desc())
        
        results = db_session.execute(stmt).scalars().all()
        
        assert len(results) == 3
        assert results[0].impressions == 1000  # Most recent
        assert results[2].impressions == 3000  # Oldest of the 3


class TestMetaModelsValidation:
    """Test data validation and constraints."""
    
    def test_unique_ad_account_id(self, db_session: Session, social_account: SocialAccountModel, meta_account: MetaAccountModel):
        """Test unique constraint on ad_account_id."""
        # Create another social account
        another_social = SocialAccountModel(
            platform="instagram",
            handle="@another",
            is_active=1,
        )
        db_session.add(another_social)
        db_session.commit()
        
        # Try to create Meta account with same ad_account_id
        duplicate = MetaAccountModel(
            social_account_id=another_social.id,
            ad_account_id=meta_account.ad_account_id,  # Duplicate!
            account_name="Duplicate",
        )
        db_session.add(duplicate)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_unique_insights_per_ad_per_day(self, db_session: Session, meta_account: MetaAccountModel):
        """Test unique constraint on ad_id + date."""
        # Create hierarchy
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_unique",
            campaign_name="Unique Test",
            objective="REACH",
            status="ACTIVE",
        )
        db_session.add(campaign)
        db_session.commit()
        
        adset = MetaAdsetModel(
            campaign_id=campaign.id,
            adset_id="ads_unique",
            adset_name="Unique Adset",
            status="ACTIVE",
        )
        db_session.add(adset)
        db_session.commit()
        
        ad = MetaAdModel(
            adset_id=adset.id,
            ad_id="ad_unique",
            ad_name="Unique Ad",
            status="ACTIVE",
        )
        db_session.add(ad)
        db_session.commit()
        
        # Create first insight
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        insight1 = MetaAdInsightsModel(
            ad_id=ad.id,
            date=today,
            impressions=5000,
        )
        db_session.add(insight1)
        db_session.commit()
        
        # Try to create duplicate insight for same ad + date
        insight2 = MetaAdInsightsModel(
            ad_id=ad.id,
            date=today,  # Same date!
            impressions=6000,
        )
        db_session.add(insight2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_creative_human_control_flags(self, db_session: Session, video_asset: VideoAsset):
        """Test human control flags on creative."""
        creative = MetaCreativeModel(
            video_asset_id=video_asset.id,
            creative_id="cre_control",
            creative_name="Control Test",
            creative_type="video",
            status="active",
            is_approved=0,
            is_reviewed=0,
        )
        db_session.add(creative)
        db_session.commit()
        
        # Simulate review
        creative.is_reviewed = 1
        creative.reviewed_by = "admin@example.com"
        creative.reviewed_at = datetime.utcnow()
        db_session.commit()
        
        # Simulate approval
        creative.is_approved = 1
        db_session.commit()
        
        assert creative.is_reviewed == 1
        assert creative.is_approved == 1
        assert creative.reviewed_by == "admin@example.com"
        assert creative.reviewed_at is not None
    
    def test_campaign_approval_workflow(self, db_session: Session, meta_account: MetaAccountModel):
        """Test campaign approval workflow."""
        campaign = MetaCampaignModel(
            meta_account_id=meta_account.id,
            campaign_id="cam_approval",
            campaign_name="Approval Test",
            objective="VIDEO_VIEWS",
            status="PAUSED",
            requires_approval=1,
            is_approved=0,
        )
        db_session.add(campaign)
        db_session.commit()
        
        # Verify needs approval
        assert campaign.requires_approval == 1
        assert campaign.is_approved == 0
        
        # Approve campaign
        campaign.is_approved = 1
        campaign.approved_by = "manager@example.com"
        campaign.approved_at = datetime.utcnow()
        db_session.commit()
        
        # Change to active after approval
        campaign.status = "ACTIVE"
        db_session.commit()
        
        assert campaign.is_approved == 1
        assert campaign.status == "ACTIVE"
        assert campaign.approved_by == "manager@example.com"
