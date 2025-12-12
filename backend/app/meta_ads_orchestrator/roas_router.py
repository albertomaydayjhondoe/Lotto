"""
ROAS API Router

Provides REST API endpoints for ROAS metrics, predictions, and outcomes.

Endpoints:
- GET /meta/roas/summary/{campaign_id} - Get ROAS summary
- GET /meta/roas/predictions/{ad_id} - Get ROAS predictions
- GET /meta/roas/outcomes/{ad_id} - Get pixel outcomes
- POST /meta/roas/refresh/{campaign_id} - Recalculate ROAS metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.permissions import require_role
from .roas_integration import ROASInsightsIntegration
from .roas_engine import ROASCalculator, PredictionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta/roas", tags=["Meta ROAS"])


# Request/Response Models
class ROASSummaryResponse(BaseModel):
    """ROAS summary response."""
    campaign_id: UUID
    date_start: datetime
    date_end: datetime
    
    # Core metrics
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    
    # ROAS metrics
    actual_roas: float
    smoothed_roas: float
    predicted_roas: Optional[float] = None
    
    # Blended metrics
    blended_ctr: float
    blended_cpc: float
    blended_cpm: float
    conversion_rate: float
    
    # Quality metrics
    session_quality_score: float
    user_retention_probability: float
    lifetime_value_estimate: float
    
    # Statistical confidence
    confidence_interval_low: float
    confidence_interval_high: float
    is_outlier: bool
    outlier_reason: Optional[str] = None
    sample_size: int


class ROASPredictionResponse(BaseModel):
    """ROAS prediction response."""
    ad_id: UUID
    predicted_roas: float
    confidence: float
    historical_data_points: int
    recent_trend: str
    
    conversion_probability: float
    credible_interval_low: float
    credible_interval_high: float
    
    expected_value: Optional[float] = None
    expected_revenue: Optional[float] = None
    breakeven_conversion_rate: Optional[float] = None
    is_profitable: Optional[bool] = None


class PixelOutcomeResponse(BaseModel):
    """Pixel outcome response."""
    id: UUID
    pixel_id: str
    event_name: str
    conversion_type: str
    value_usd: Optional[float] = None
    
    ad_id: Optional[UUID] = None
    adset_id: Optional[UUID] = None
    campaign_id: UUID
    
    session_duration_seconds: Optional[int] = None
    landing_path: Optional[str] = None
    
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None
    
    attribution_model: str
    attribution_weight: float
    confidence_score: Optional[float] = None
    
    event_timestamp: datetime
    time_to_conversion_seconds: Optional[int] = None


class RefreshRequest(BaseModel):
    """Request to refresh ROAS metrics."""
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    recalculate_all: bool = Field(default=False, description="Recalculate all ads in campaign")


class RefreshResponse(BaseModel):
    """Response from refresh operation."""
    success: bool
    metrics_calculated: int
    errors: list[str] = Field(default_factory=list)
    calculation_time_seconds: float


# Endpoints
@router.get(
    "/summary/{campaign_id}",
    response_model=ROASSummaryResponse,
    dependencies=[Depends(require_role("admin", "manager"))],
)
async def get_roas_summary(
    campaign_id: UUID,
    date_start: Optional[datetime] = Query(None, description="Start date (default: 7 days ago)"),
    date_end: Optional[datetime] = Query(None, description="End date (default: today)"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive ROAS summary for campaign.
    
    Combines Meta Ads Insights with Pixel Outcomes to provide:
    - Real ROAS from conversions
    - Blended CTR, CPC, CPM
    - Conversion rate
    - Quality scores
    - Statistical confidence intervals
    """
    try:
        integration = ROASInsightsIntegration(session)
        
        metrics = await integration.calculate_blended_metrics(
            campaign_id=campaign_id,
            date_start=date_start,
            date_end=date_end,
        )
        
        # Get predictions
        prediction_engine = PredictionEngine(session)
        predictions = await prediction_engine.predict_roas(
            campaign_id=campaign_id,
            lookback_days=30,
        )
        
        return ROASSummaryResponse(
            campaign_id=campaign_id,
            date_start=metrics["date_start"],
            date_end=metrics["date_end"],
            impressions=metrics["impressions"],
            clicks=metrics["clicks"],
            conversions=metrics["conversions"],
            spend=metrics["spend"],
            revenue=metrics["total_revenue"],
            actual_roas=metrics["actual_roas"],
            smoothed_roas=metrics["smoothed_roas"],
            predicted_roas=predictions.get("predicted_roas"),
            blended_ctr=metrics["blended_ctr"],
            blended_cpc=metrics["blended_cpc"],
            blended_cpm=metrics["blended_cpm"],
            conversion_rate=metrics["conversion_rate"],
            session_quality_score=metrics["session_quality_score"],
            user_retention_probability=metrics["user_retention_probability"],
            lifetime_value_estimate=metrics["lifetime_value_estimate"],
            confidence_interval_low=metrics["confidence_interval_low"],
            confidence_interval_high=metrics["confidence_interval_high"],
            is_outlier=metrics["is_outlier"],
            outlier_reason=metrics.get("outlier_reason"),
            sample_size=metrics["sample_size"],
        )
    
    except Exception as e:
        logger.error(f"Error getting ROAS summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/predictions/{ad_id}",
    response_model=ROASPredictionResponse,
    dependencies=[Depends(require_role("admin", "manager"))],
)
async def get_roas_predictions(
    ad_id: UUID,
    lookback_days: int = Query(30, ge=7, le=90, description="Days of historical data"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get ROAS predictions and conversion probability for ad.
    
    Provides:
    - Predicted ROAS based on historical trends
    - Conversion probability with Bayesian inference
    - Expected value per click
    - Breakeven metrics
    """
    try:
        prediction_engine = PredictionEngine(session)
        
        # Get ROAS predictions
        roas_pred = await prediction_engine.predict_roas(
            ad_id=ad_id,
            lookback_days=lookback_days,
        )
        
        # Get insights for conversion probability
        roas_calc = ROASCalculator(session)
        clicks = await roas_calc._get_clicks(
            ad_id=ad_id,
            campaign_id=None,
            adset_id=None,
            date_start=datetime.utcnow() - timedelta(days=lookback_days),
            date_end=datetime.utcnow(),
        )
        
        outcomes = await roas_calc._get_pixel_outcomes(
            ad_id=ad_id,
            campaign_id=None,
            adset_id=None,
            date_start=datetime.utcnow() - timedelta(days=lookback_days),
            date_end=datetime.utcnow(),
        )
        
        conversions = len(outcomes)
        
        # Calculate conversion probability
        conv_prob = prediction_engine.calculate_conversion_probability(
            clicks=clicks,
            conversions=conversions,
        )
        
        # Calculate expected value if we have data
        expected_value_data = None
        if conversions > 0 and clicks > 0:
            avg_order_value = sum(o.value_usd or 0 for o in outcomes) / conversions
            spend = await roas_calc._get_ad_spend(
                ad_id=ad_id,
                campaign_id=None,
                adset_id=None,
                date_start=datetime.utcnow() - timedelta(days=lookback_days),
                date_end=datetime.utcnow(),
            )
            cpc = spend / clicks if clicks > 0 else 0
            
            expected_value_data = prediction_engine.calculate_expected_value(
                conversion_probability=conv_prob["probability"],
                average_order_value=avg_order_value,
                cost_per_click=cpc,
            )
        
        return ROASPredictionResponse(
            ad_id=ad_id,
            predicted_roas=roas_pred["predicted_roas"],
            confidence=roas_pred["confidence"],
            historical_data_points=roas_pred["historical_data_points"],
            recent_trend=roas_pred.get("recent_trend", "stable"),
            conversion_probability=conv_prob["probability"],
            credible_interval_low=conv_prob["credible_interval_low"],
            credible_interval_high=conv_prob["credible_interval_high"],
            expected_value=expected_value_data.get("expected_value") if expected_value_data else None,
            expected_revenue=expected_value_data.get("expected_revenue") if expected_value_data else None,
            breakeven_conversion_rate=expected_value_data.get("breakeven_conversion_rate") if expected_value_data else None,
            is_profitable=expected_value_data.get("is_profitable") if expected_value_data else None,
        )
    
    except Exception as e:
        logger.error(f"Error getting ROAS predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/outcomes/{ad_id}",
    response_model=list[PixelOutcomeResponse],
    dependencies=[Depends(require_role("admin", "manager"))],
)
async def get_pixel_outcomes(
    ad_id: UUID,
    date_start: Optional[datetime] = Query(None, description="Start date (default: 7 days ago)"),
    date_end: Optional[datetime] = Query(None, description="End date (default: today)"),
    limit: int = Query(100, ge=1, le=1000, description="Max outcomes to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get pixel conversion outcomes for ad.
    
    Returns detailed pixel event data including:
    - Conversion events (purchases, leads, etc.)
    - Session information
    - UTM tracking
    - Attribution details
    """
    try:
        if not date_end:
            date_end = datetime.utcnow()
        if not date_start:
            date_start = date_end - timedelta(days=7)
        
        roas_calc = ROASCalculator(session)
        outcomes = await roas_calc._get_pixel_outcomes(
            ad_id=ad_id,
            campaign_id=None,
            adset_id=None,
            date_start=date_start,
            date_end=date_end,
        )
        
        # Limit results
        outcomes = outcomes[:limit]
        
        return [
            PixelOutcomeResponse(
                id=o.id,
                pixel_id=o.pixel_id,
                event_name=o.event_name,
                conversion_type=o.conversion_type,
                value_usd=o.value_usd,
                ad_id=o.ad_id,
                adset_id=o.adset_id,
                campaign_id=o.campaign_id,
                session_duration_seconds=o.session_duration_seconds,
                landing_path=o.landing_path,
                utm_source=o.utm_source,
                utm_campaign=o.utm_campaign,
                attribution_model=o.attribution_model,
                attribution_weight=o.attribution_weight,
                confidence_score=o.confidence_score,
                event_timestamp=o.event_timestamp,
                time_to_conversion_seconds=o.time_to_conversion_seconds,
            )
            for o in outcomes
        ]
    
    except Exception as e:
        logger.error(f"Error getting pixel outcomes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refresh/{campaign_id}",
    response_model=RefreshResponse,
    dependencies=[Depends(require_role("admin", "manager"))],
)
async def refresh_roas_metrics(
    campaign_id: UUID,
    request: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Recalculate ROAS metrics for campaign.
    
    Updates MetaROASMetricsModel with latest data from:
    - Meta Ads Insights
    - Pixel Outcomes
    
    Can recalculate for specific date range or all ads in campaign.
    """
    start_time = datetime.utcnow()
    
    try:
        integration = ROASInsightsIntegration(session)
        
        date_start = request.date_start
        date_end = request.date_end
        
        if not date_end:
            date_end = datetime.utcnow()
        if not date_start:
            date_start = date_end - timedelta(days=7)
        
        metrics_calculated = 0
        errors = []
        
        if request.recalculate_all:
            # Get all ads in campaign
            from sqlalchemy import select
            from app.models.database import MetaAdModel
            
            query = select(MetaAdModel).where(MetaAdModel.campaign_id == campaign_id)
            result = await session.execute(query)
            ads = result.scalars().all()
            
            # Calculate metrics for each ad
            for ad in ads:
                try:
                    await integration.save_roas_metrics(
                        campaign_id=campaign_id,
                        ad_id=ad.id,
                        date=date_end.replace(hour=0, minute=0, second=0, microsecond=0),
                    )
                    metrics_calculated += 1
                except Exception as e:
                    logger.error(f"Error calculating metrics for ad {ad.id}: {e}")
                    errors.append(f"Ad {ad.id}: {str(e)}")
        else:
            # Calculate for campaign level only
            await integration.save_roas_metrics(
                campaign_id=campaign_id,
                date=date_end.replace(hour=0, minute=0, second=0, microsecond=0),
            )
            metrics_calculated = 1
        
        end_time = datetime.utcnow()
        calculation_time = (end_time - start_time).total_seconds()
        
        return RefreshResponse(
            success=len(errors) == 0,
            metrics_calculated=metrics_calculated,
            errors=errors,
            calculation_time_seconds=calculation_time,
        )
    
    except Exception as e:
        logger.error(f"Error refreshing ROAS metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
