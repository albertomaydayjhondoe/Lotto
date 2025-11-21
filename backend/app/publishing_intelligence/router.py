"""
FastAPI router for Publishing Intelligence Layer (APIL)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.publishing_intelligence.models import (
    AutoScheduleRequest,
    AutoScheduleResponse,
    GlobalForecast,
    PriorityCalculation,
    PriorityRequest
)
from app.publishing_intelligence.intelligence import (
    auto_schedule_clip,
    get_global_forecast,
    calculate_priority
)


router = APIRouter()


@router.post("/auto-schedule", response_model=AutoScheduleResponse)
async def auto_schedule_endpoint(
    request: AutoScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-schedule a clip using intelligence layer
    
    This endpoint:
    1. Calculates priority for the clip
    2. Gets current forecast
    3. Selects optimal slot
    4. Resolves conflicts by priority
    5. Creates scheduled PublishLog
    
    Example request:
    ```json
    {
      "clip_id": "clip_123",
      "platform": "instagram",
      "social_account_id": "acc_456"
    }
    ```
    
    Example response:
    ```json
    {
      "publish_log_id": "log_789",
      "clip_id": "clip_123",
      "platform": "instagram",
      "scheduled_for": "2024-01-15T20:00:00Z",
      "priority": 75.5,
      "conflict_info": {
        "detected": false
      },
      "reason": "Scheduled with priority 75.5"
    }
    ```
    """
    try:
        result = await auto_schedule_clip(
            db=db,
            clip_id=request.clip_id,
            platform=request.platform,
            social_account_id=request.social_account_id,
            force_slot=request.force_slot
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-schedule failed: {str(e)}")


@router.get("/forecast", response_model=GlobalForecast)
async def get_forecast_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Get global forecast for all platforms
    
    Returns available slots, saturation risk, and scheduling information
    for Instagram, TikTok, and YouTube.
    
    Example response:
    ```json
    {
      "forecast_date": "2024-01-15T14:30:00Z",
      "instagram": {
        "platform": "instagram",
        "next_slot": "2024-01-15T18:00:00Z",
        "slots_remaining_today": 3,
        "risk": "low",
        "scheduled_count": 2,
        "window_start_hour": 18,
        "window_end_hour": 23,
        "min_gap_minutes": 60
      },
      "tiktok": {
        "platform": "tiktok",
        "next_slot": "2024-01-15T16:30:00Z",
        "slots_remaining_today": 5,
        "risk": "medium",
        "scheduled_count": 8,
        "window_start_hour": 16,
        "window_end_hour": 24,
        "min_gap_minutes": 30
      },
      "youtube": {
        "platform": "youtube",
        "next_slot": "2024-01-15T17:00:00Z",
        "slots_remaining_today": 2,
        "risk": "high",
        "scheduled_count": 3,
        "window_start_hour": 17,
        "window_end_hour": 22,
        "min_gap_minutes": 90
      }
    }
    ```
    """
    try:
        forecast = await get_global_forecast(db)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")


@router.get("/priority/{clip_id}", response_model=PriorityCalculation)
async def get_priority_endpoint(
    clip_id: str,
    platform: str = "instagram",
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate priority for a specific clip
    
    Returns detailed priority breakdown showing contribution from:
    - Visual score (40%)
    - Engagement score (30%)
    - Predicted virality (20%)
    - Campaign weight (10%)
    - Delay penalty (bonus for older clips)
    
    Example response:
    ```json
    {
      "clip_id": "clip_123",
      "priority": 75.5,
      "visual_score": 85.0,
      "engagement_score": 70.0,
      "predicted_virality": 60.0,
      "campaign_weight": 50.0,
      "delay_penalty": 10.0,
      "breakdown": {
        "visual_score_contribution": 34.0,
        "engagement_score_contribution": 21.0,
        "predicted_virality_contribution": 12.0,
        "campaign_weight_contribution": 5.0,
        "delay_penalty_contribution": 10.0
      }
    }
    ```
    """
    try:
        priority = await calculate_priority(db, clip_id, platform)
        return priority
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Priority calculation failed: {str(e)}")
