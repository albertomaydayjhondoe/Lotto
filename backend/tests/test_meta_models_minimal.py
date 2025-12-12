"""
Minimal tests to validate Meta Ads models can be created and saved
Based on test_publishing_models.py pattern
"""
import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from app.models.database import (
    SocialAccountModel,
    MetaAccountModel,
    MetaCampaignModel,
)


@pytest.mark.asyncio
async def test_meta_account_creation(db_session):
    """Test Meta account can be created (links to social account)"""
    # First create social account
    social_account = SocialAccountModel(
        id=uuid4(),
        platform="instagram",
        handle="@test_meta",
        is_active=1
    )
    db_session.add(social_account)
    await db_session.commit()
    
    # Verify social account was created
    stmt = select(SocialAccountModel).where(SocialAccountModel.handle == "@test_meta")
    result = await db_session.execute(stmt)
    social = result.scalar_one()
    
    assert social.id is not None
    assert social.handle == "@test_meta"
    
    # Now create Meta account
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_123456",
        account_name="Test Meta Ad Account",
        currency="USD",
        timezone="America/New_York"
    )
    db_session.add(meta)
    await db_session.commit()
    
    # Query Meta account back
    stmt = select(MetaAccountModel).where(MetaAccountModel.ad_account_id == "act_123456")
    result = await db_session.execute(stmt)
    meta_account = result.scalar_one()
    
    assert meta_account.id is not None
    assert meta_account.ad_account_id == "act_123456"
    assert meta_account.social_account_id == social.id
    assert meta_account.currency == "USD"


@pytest.mark.asyncio
async def test_meta_campaign_creation(db_session):
    """Test Meta campaign can be created with human control flags"""
    # Setup: social + meta account
    social = SocialAccountModel(
        id=uuid4(),
        platform="facebook",
        handle="@test_fb",
        is_active=1
    )
    db_session.add(social)
    await db_session.commit()
    
    meta = MetaAccountModel(
        social_account_id=social.id,
        ad_account_id="act_999888",
        account_name="Test Account",
        currency="USD"
    )
    db_session.add(meta)
    await db_session.commit()
    
    # Create campaign
    campaign = MetaCampaignModel(
        meta_account_id=meta.id,
        campaign_id="camp_abc123",
        campaign_name="Black Friday Sale",
        objective="CONVERSIONS",
        status="PAUSED",
        daily_budget=200.0,
        requires_approval=1,  # Requires human approval
        utm_source="facebook",
        utm_medium="paid",
        utm_campaign="black-friday-2024"
    )
    db_session.add(campaign)
    await db_session.commit()
    
    # Query back
    stmt = select(MetaCampaignModel).where(MetaCampaignModel.campaign_id == "camp_abc123")
    result = await db_session.execute(stmt)
    camp = result.scalar_one()
    
    assert camp.id is not None
    assert camp.campaign_name == "Black Friday Sale"
    assert camp.requires_approval == 1
    assert camp.is_approved == 0  # Not yet approved
    assert camp.utm_campaign == "black-friday-2024"

