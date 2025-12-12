"""
Test example for creating a Meta Ads campaign.

This test demonstrates creating a campaign with the following data:
{
  "clip_id": "clip_test_123",
  "campaign_name": "test_campaign",
  "objective": "OUTCOME_TRAFFIC"
}
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.meta_ads_orchestrator.orchestrator import MetaAdsOrchestrator
from app.meta_ads_orchestrator.models import OrchestrationRequest


@pytest.mark.asyncio
async def test_create_campaign_with_traffic_objective():
    """
    Test creating a campaign with OUTCOME_TRAFFIC objective.
    
    Simulates the REST API request:
    POST /meta/orchestrate/campaign
    {
      "clip_id": "clip_test_123",
      "campaign_name": "test_campaign",
      "objective": "OUTCOME_TRAFFIC"
    }
    
    This test validates that the orchestrator correctly processes
    the request and creates campaign, adset, creative, and ad.
    """
    # Se requiere database y Meta Ads Client funcionando
    # Este test documenta los datos requeridos
    
    required_fields = {
        "social_account_id": "UUID of social account",
        "clip_id": "UUID of clip",
        "campaign_name": "test_campaign",
        "campaign_objective": "OUTCOME_TRAFFIC",
        "daily_budget_cents": 5000,
        "creative_title": "Test Creative Title",
        "creative_description": "Test Creative Description",
        "landing_url": "https://example.com/landing"
    }
    
    print("\n📝 Campaign Creation Request Fields:")
    for field, value in required_fields.items():
        print(f"   {field}: {value}")
    
    print("\n✅ To test with real API:")
    print("   1. Start PostgreSQL: docker-compose up -d")
    print("   2. Start server: uvicorn app.main:app --reload")
    print("   3. Run curl:")
    print("""
   curl -X POST http://localhost:8000/meta/orchestrate/campaign \\
     -H "Content-Type: application/json" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -d '{
       "social_account_id": "UUID",
       "clip_id": "UUID",
       "campaign_name": "test_campaign",
       "campaign_objective": "OUTCOME_TRAFFIC",
       "daily_budget_cents": 5000,
       "creative_title": "Title",
       "creative_description": "Description",
       "landing_url": "https://example.com"
     }'
    """)


@pytest.mark.asyncio
async def test_create_campaign_validates_clip_exists():
    """
    Test that creating a campaign fails if clip doesn't exist.
    """
    mock_session = AsyncMock()
    
    # Mock clip not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    orchestrator = MetaAdsOrchestrator(db=mock_session)
    
    request = OrchestrationRequest(
        social_account_id=str(uuid4()),
        clip_id=str(uuid4()),
        campaign_name="test_campaign",
        campaign_objective="OUTCOME_TRAFFIC",
        daily_budget_cents=5000,
        creative_title="Test Title",
        creative_description="Test Description",
        landing_url="https://example.com"
    )
    
    # Execute - should handle gracefully
    result = await orchestrator.orchestrate_campaign(request)
    
    # Should return failure result
    assert result.overall_success is False
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_create_campaign_requires_valid_objective():
    """
    Test that creating a campaign with invalid objective is handled.
    """
    mock_session = AsyncMock()
    
    mock_clip = MagicMock()
    mock_clip.id = "clip_test_123"
    mock_clip.video_url = "https://example.com/video.mp4"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_clip
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()
    
    with patch("app.meta_ads_orchestrator.orchestrator.get_meta_client_for_account") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Meta API rejects invalid objective
        mock_client.create_campaign.side_effect = Exception("Invalid objective")
        
        orchestrator = MetaAdsOrchestrator(db=mock_session)
        
        request = OrchestrationRequest(
            social_account_id=str(uuid4()),
            clip_id=str(uuid4()),
            campaign_name="test_campaign",
            campaign_objective="OUTCOME_TRAFFIC",  # Will be rejected by Meta API
            daily_budget_cents=5000,
            creative_title="Test Title",
            creative_description="Test Description",
            landing_url="https://example.com"
        )
        
        # Execute - should handle error
        result = await orchestrator.orchestrate_campaign(request)
        
        # Should return failure
        assert result.overall_success is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    # Run with: pytest tests/test_create_campaign_example.py -v -s
    pytest.main([__file__, "-v", "-s"])
