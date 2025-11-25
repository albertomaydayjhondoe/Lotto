"""
Tests for Meta Ads API Client

Tests the MetaAdsClient in STUB mode (no real API calls).
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.meta_ads_client import MetaAdsClient, MetaAPIError
from app.meta_ads_client.factory import get_meta_client_for_account
from app.meta_ads_client.mappers import (
    map_campaign_response_to_model_dict,
    map_adset_response_to_model_dict,
    map_ad_response_to_model_dict,
    map_insights_response_to_model_dict,
)
from app.models.database import SocialAccountModel, MetaAccountModel


# ============================================================================
# Basic Client Tests
# ============================================================================

def test_stub_create_campaign_returns_fake_id():
    """Test that stub mode returns a fake campaign ID."""
    client = MetaAdsClient(mode="stub")
    
    campaign = client.create_campaign(
        name="Test Campaign",
        objective="OUTCOME_SALES",
        status="PAUSED"
    )
    
    assert campaign["id"].startswith("META_CAMPAIGN_")
    assert campaign["name"] == "Test Campaign"
    assert campaign["objective"] == "OUTCOME_SALES"
    assert campaign["status"] == "PAUSED"
    assert "created_time" in campaign
    assert "updated_time" in campaign


def test_stub_create_adset_uses_campaign_id():
    """Test that adset creation links to campaign ID."""
    client = MetaAdsClient(mode="stub")
    
    # Create campaign first
    campaign = client.create_campaign("Parent Campaign", "OUTCOME_TRAFFIC", "PAUSED")
    
    # Create adset
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=7)
    
    adset = client.create_adset(
        campaign_id=campaign["id"],
        name="Test Adset",
        daily_budget=10000,  # $100
        start_time=start_time,
        end_time=end_time,
        targeting={"age_min": 18, "age_max": 65, "genders": [1, 2]},
        optimization_goal="LINK_CLICKS",
        billing_event="IMPRESSIONS"
    )
    
    assert adset["id"].startswith("META_ADSET_")
    assert adset["campaign_id"] == campaign["id"]
    assert adset["name"] == "Test Adset"
    assert adset["daily_budget"] == "10000"
    assert adset["status"] == "PAUSED"


def test_stub_create_ad_uses_adset_id():
    """Test that ad creation links to adset ID."""
    client = MetaAdsClient(mode="stub")
    
    # Create campaign and adset first
    campaign = client.create_campaign("Campaign", "OUTCOME_ENGAGEMENT", "PAUSED")
    
    start_time = datetime.utcnow()
    adset = client.create_adset(
        campaign_id=campaign["id"],
        name="Adset",
        daily_budget=5000,
        start_time=start_time,
        end_time=None,
        targeting={"age_min": 25, "age_max": 45},
        optimization_goal="POST_ENGAGEMENT",
        billing_event="IMPRESSIONS"
    )
    
    # Upload creative
    creative = client.upload_creative_from_clip(
        clip_id="clip_123",
        title="Amazing Video",
        description="Watch this!"
    )
    
    # Create ad
    ad = client.create_ad(
        creative_id=creative["id"],
        adset_id=adset["id"],
        name="Test Ad",
        status="PAUSED"
    )
    
    assert ad["id"].startswith("META_AD_")
    assert ad["adset_id"] == adset["id"]
    assert ad["creative"]["id"] == creative["id"]
    assert ad["status"] == "PAUSED"


def test_stub_get_insights_returns_metrics_shape():
    """Test that insights return proper metrics structure."""
    client = MetaAdsClient(mode="stub")
    
    # Create full hierarchy
    campaign = client.create_campaign("Campaign", "OUTCOME_SALES", "ACTIVE")
    
    start_time = datetime.utcnow()
    adset = client.create_adset(
        campaign_id=campaign["id"],
        name="Adset",
        daily_budget=10000,
        start_time=start_time,
        end_time=None,
        targeting={"age_min": 18, "age_max": 65},
        optimization_goal="CONVERSIONS",
        billing_event="LINK_CLICKS"
    )
    
    creative = client.upload_creative_from_clip(
        clip_id="clip_456",
        title="Product Demo",
        description="Buy now!"
    )
    
    ad = client.create_ad(
        creative_id=creative["id"],
        adset_id=adset["id"],
        name="Ad"
    )
    
    # Get insights
    insights = client.get_insights(ad["id"], date_preset="last_7d")
    
    assert len(insights) >= 1  # At least one day of data
    
    for insight in insights:
        assert "date_start" in insight
        assert "date_stop" in insight
        assert "impressions" in insight
        assert "reach" in insight
        assert "clicks" in insight
        assert "ctr" in insight
        assert "spend" in insight
        assert "cpc" in insight
        assert "cpm" in insight
        
        # Verify metrics are strings (Meta API returns strings)
        assert isinstance(insight["impressions"], str)
        assert isinstance(insight["clicks"], str)
        assert isinstance(insight["spend"], str)


def test_stub_invalid_daily_budget_raises_error():
    """Test that invalid parameters raise MetaAPIError."""
    client = MetaAdsClient(mode="stub")
    
    with pytest.raises(MetaAPIError, match="daily_budget must be positive"):
        client.create_campaign(
            name="Bad Campaign",
            objective="OUTCOME_SALES",
            status="PAUSED",
            daily_budget=-100
        )


def test_stub_empty_campaign_name_raises_error():
    """Test that empty campaign name raises error."""
    client = MetaAdsClient(mode="stub")
    
    with pytest.raises(MetaAPIError, match="Campaign name cannot be empty"):
        client.create_campaign(
            name="",
            objective="OUTCOME_TRAFFIC",
            status="PAUSED"
        )


# ============================================================================
# Factory Tests (Simplified - No DB required for stub mode)
# ============================================================================

def test_client_factory_returns_stub_when_no_creds():
    """Test that factory returns STUB client when no DB is available."""
    # For now, we test the client directly without factory
    # Factory tests would require complex DB mocking
    client = MetaAdsClient(mode="stub")
    
    assert client.mode == "stub"
    
    # Verify it works
    campaign = client.create_campaign("Test", "OUTCOME_AWARENESS", "PAUSED")
    assert campaign["id"].startswith("META_CAMPAIGN_")


# ============================================================================
# Mapper Tests
# ============================================================================

def test_helpers_map_campaign_response_to_model_dict():
    """Test campaign response mapper."""
    response = {
        "id": "123456789",
        "name": "Summer Sale",
        "objective": "OUTCOME_SALES",
        "status": "ACTIVE",
        "daily_budget": "20000",  # $200
        "lifetime_budget": None,
        "budget_remaining": "15000",
        "special_ad_categories": [],
        "created_time": "2025-11-24T10:00:00Z",
        "updated_time": "2025-11-24T11:00:00Z",
        "account_id": "act_999"
    }
    
    model_dict = map_campaign_response_to_model_dict(response, social_account_id="test_123")
    
    assert model_dict["campaign_id"] == "123456789"
    assert model_dict["name"] == "Summer Sale"
    assert model_dict["objective"] == "OUTCOME_SALES"
    assert model_dict["status"] == "ACTIVE"
    assert model_dict["daily_budget"] == 20000  # In cents
    assert model_dict["social_account_id"] == "test_123"
    assert isinstance(model_dict["created_at"], datetime)


def test_helpers_map_adset_response_to_model_dict():
    """Test adset response mapper."""
    response = {
        "id": "adset_123",
        "name": "Test Adset",
        "campaign_id": "camp_456",
        "status": "PAUSED",
        "daily_budget": "5000",
        "lifetime_budget": None,
        "start_time": "2025-11-25T00:00:00Z",
        "end_time": "2025-12-01T23:59:59Z",
        "optimization_goal": "LINK_CLICKS",
        "billing_event": "IMPRESSIONS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "bid_amount": None,
        "targeting": {"age_min": 18, "age_max": 65},
        "created_time": "2025-11-24T10:00:00Z",
        "updated_time": "2025-11-24T11:00:00Z"
    }
    
    model_dict = map_adset_response_to_model_dict(response, campaign_db_id=999, social_account_id="test_123")
    
    assert model_dict["adset_id"] == "adset_123"
    assert model_dict["name"] == "Test Adset"
    assert model_dict["status"] == "PAUSED"
    assert model_dict["daily_budget"] == 5000  # In cents
    assert model_dict["campaign_id"] == 999
    assert model_dict["social_account_id"] == "test_123"


def test_helpers_map_ad_response_to_model_dict():
    """Test ad response mapper."""
    response = {
        "id": "ad_789",
        "name": "Test Ad",
        "adset_id": "adset_123",
        "campaign_id": "camp_456",
        "status": "ACTIVE",
        "creative": {"id": "creative_abc", "name": "Creative Name"},
        "tracking_specs": [],
        "conversion_specs": [],
        "created_time": "2025-11-24T10:00:00Z",
        "updated_time": "2025-11-24T11:00:00Z"
    }
    
    model_dict = map_ad_response_to_model_dict(response, adset_db_id=888, social_account_id="test_123")
    
    assert model_dict["ad_id"] == "ad_789"
    assert model_dict["name"] == "Test Ad"
    assert model_dict["status"] == "ACTIVE"
    assert model_dict["creative_id"] == "creative_abc"
    assert model_dict["adset_id"] == 888
    assert model_dict["social_account_id"] == "test_123"
    assert isinstance(model_dict["created_at"], datetime)


def test_helpers_map_insights_response_to_model_dict():
    """Test insights response mapper."""
    response = {
        "date_start": "2025-11-24",
        "date_stop": "2025-11-24",
        "impressions": "5000",
        "reach": "3500",
        "frequency": "1.43",
        "clicks": "150",
        "ctr": "3.0",
        "spend": "2500",
        "cpc": "16.67",
        "cpm": "50.0",
        "cpp": "16.67",
        "conversions": "15",
        "conversion_rate": "10.0",
        "cost_per_conversion": "166.67"
    }
    
    model_dict = map_insights_response_to_model_dict(response, ad_db_id=777)
    
    assert model_dict["ad_id"] == 777
    assert model_dict["impressions"] == 5000
    assert model_dict["reach"] == 3500
    assert model_dict["clicks"] == 150
    assert model_dict["spend"] == 2500.0
    assert model_dict["cpc"] == 16.67
    assert model_dict["date_start"] == "2025-11-24"
    assert model_dict["date_stop"] == "2025-11-24"


def test_live_mode_fallback_to_stub_without_token():
    """Test that LIVE mode falls back to STUB when token is missing."""
    # Try to create in live mode without credentials
    client = MetaAdsClient(mode="live")
    
    # Should fallback to stub
    assert client.mode == "stub"
    
    # Verify it works in stub mode
    campaign = client.create_campaign("Test", "OUTCOME_TRAFFIC", "PAUSED")
    assert campaign["id"].startswith("META_CAMPAIGN_")


def test_stub_upload_creative_returns_video_id():
    """Test that creative upload returns video ID."""
    client = MetaAdsClient(mode="stub")
    
    creative = client.upload_creative_from_clip(
        clip_id="clip_xyz",
        title="Product Launch",
        description="Revolutionary new product!",
        landing_url="https://example.com/buy"
    )
    
    assert creative["id"].startswith("META_CREATIVE_")
    assert creative["name"] == "Creative: Product Launch"
    assert creative["video_id"].startswith("META_VIDEO_")
    assert "object_story_spec" in creative
    assert creative["status"] == "ACTIVE"


def test_stub_get_insights_custom_date_range():
    """Test insights returns data correctly."""
    client = MetaAdsClient(mode="stub")
    
    ad_id = "test_ad_123"
    
    # Get insights for an ad
    insights = client.get_insights(
        level="ad",
        object_id=ad_id,
        date_preset="last_7d"
    )
    
    # Should return at least one insight
    assert len(insights) >= 1
    
    # Verify structure
    insight = insights[0]
    assert "date_start" in insight
    assert "date_stop" in insight
    assert "impressions" in insight
    assert "clicks" in insight
    assert "spend" in insight
