"""
ROAS Insights Integration Module

Combines Meta Ad Insights with Pixel Outcomes to produce comprehensive metrics:
- Blended ROAS (insights + conversions)
- Blended CTR
- Session quality scores
- User retention predictions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    MetaAdInsightsModel,
    MetaPixelOutcomeModel,
    MetaConversionEventModel,
    MetaROASMetricsModel,
)
from .roas_engine import ROASCalculator, PredictionEngine

logger = logging.getLogger(__name__)


class ROASInsightsIntegration:
    """
    Integrates Meta Ads Insights with Pixel Outcomes for comprehensive metrics.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roas_calculator = ROASCalculator(session)
        self.prediction_engine = PredictionEngine(session)
    
    async def calculate_blended_metrics(
        self,
        campaign_id: Optional[UUID] = None,
        adset_id: Optional[UUID] = None,
        ad_id: Optional[UUID] = None,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate blended metrics combining insights and pixel outcomes.
        
        Args:
            campaign_id: Campaign UUID
            adset_id: Adset UUID
            ad_id: Ad UUID
            date_start: Start date
            date_end: End date
            
        Returns:
            Dict with blended metrics
        """
        # Default date range: last 7 days
        if not date_end:
            date_end = datetime.utcnow()
        if not date_start:
            date_start = date_end - timedelta(days=7)
        
        # Get insights data
        insights = await self._get_insights(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Get pixel outcomes
        outcomes = await self._get_outcomes(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Calculate ROAS
        roas_data = await self.roas_calculator.calculate_roas(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Calculate blended CTR
        total_impressions = sum(i.impressions or 0 for i in insights)
        total_clicks = sum(i.clicks or 0 for i in insights)
        total_conversions = len(outcomes)
        
        blended_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0.0
        
        # Calculate blended CPC and CPM
        total_spend = sum(i.spend or 0 for i in insights)
        blended_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
        blended_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0.0
        
        # Session quality score
        session_quality = await self._calculate_session_quality(outcomes)
        
        # User retention probability
        retention_prob = await self._calculate_retention_probability(outcomes)
        
        # Lifetime value estimate
        ltv_estimate = await self._estimate_lifetime_value(outcomes)
        
        return {
            # Core metrics
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "spend": total_spend,
            
            # ROAS metrics
            "actual_roas": roas_data["actual_roas"],
            "smoothed_roas": roas_data["smoothed_roas"],
            "total_revenue": roas_data["total_revenue_usd"],
            
            # Blended metrics
            "blended_ctr": blended_ctr,
            "blended_cpc": blended_cpc,
            "blended_cpm": blended_cpm,
            "conversion_rate": conversion_rate,
            
            # Quality metrics
            "session_quality_score": session_quality,
            "user_retention_probability": retention_prob,
            "lifetime_value_estimate": ltv_estimate,
            
            # Statistical confidence
            "confidence_interval_low": roas_data["confidence_interval_low"],
            "confidence_interval_high": roas_data["confidence_interval_high"],
            "is_outlier": roas_data["is_outlier"],
            "outlier_reason": roas_data.get("outlier_reason"),
            
            # Metadata
            "date_start": date_start,
            "date_end": date_end,
            "sample_size": roas_data["sample_size"],
        }
    
    async def save_roas_metrics(
        self,
        campaign_id: Optional[UUID] = None,
        adset_id: Optional[UUID] = None,
        ad_id: Optional[UUID] = None,
        date: Optional[datetime] = None,
    ) -> MetaROASMetricsModel:
        """
        Calculate and save ROAS metrics to database.
        
        Args:
            campaign_id: Campaign UUID
            adset_id: Adset UUID
            ad_id: Ad UUID
            date: Date for metrics (default: today)
            
        Returns:
            MetaROASMetricsModel instance
        """
        if not date:
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        date_start = date
        date_end = date + timedelta(days=1)
        
        # Calculate blended metrics
        metrics = await self.calculate_blended_metrics(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Get predictions
        predictions = await self.prediction_engine.predict_roas(
            campaign_id, adset_id, ad_id, lookback_days=30
        )
        
        # Calculate conversion probability
        conv_prob = self.prediction_engine.calculate_conversion_probability(
            clicks=metrics["clicks"],
            conversions=metrics["conversions"],
        )
        
        # Determine performance tier
        performance_tier = self._determine_performance_tier(
            metrics["actual_roas"], metrics["conversion_rate"]
        )
        
        # Generate recommendation
        recommendation, budget_change_pct = self._generate_recommendation(
            metrics["actual_roas"],
            metrics["smoothed_roas"],
            predictions["predicted_roas"],
            performance_tier,
        )
        
        # Create or update ROAS metrics record
        roas_metrics = MetaROASMetricsModel(
            campaign_id=campaign_id,
            adset_id=adset_id,
            ad_id=ad_id,
            date=date,
            date_start=date_start,
            date_end=date_end,
            
            # ROAS metrics
            actual_roas=metrics["actual_roas"],
            predicted_roas=predictions["predicted_roas"],
            blended_roas=metrics["smoothed_roas"],
            
            # Revenue and cost
            total_revenue_usd=metrics["total_revenue"],
            total_cost_usd=metrics["spend"],
            
            # Conversion metrics
            total_conversions=metrics["conversions"],
            conversion_rate=metrics["conversion_rate"],
            conversion_probability=conv_prob["probability"],
            
            # Statistical confidence
            confidence_score=predictions["confidence"],
            confidence_interval_low=metrics["confidence_interval_low"],
            confidence_interval_high=metrics["confidence_interval_high"],
            sample_size=metrics["sample_size"],
            
            # Bayesian smoothing (using smoothed ROAS as posterior)
            prior_roas=2.0,  # Default prior
            posterior_roas=metrics["smoothed_roas"],
            smoothing_factor=0.2,
            
            # Performance indicators
            is_outlier=1 if metrics["is_outlier"] else 0,
            outlier_reason=metrics.get("outlier_reason"),
            performance_tier=performance_tier,
            
            # Optimization recommendations
            recommendation=recommendation,
            recommended_budget_change_pct=budget_change_pct,
            
            # Quality scores
            session_quality_score=metrics["session_quality_score"],
            user_retention_probability=metrics["user_retention_probability"],
            lifetime_value_estimate=metrics["lifetime_value_estimate"],
            
            # Blended metrics
            blended_ctr=metrics["blended_ctr"],
            blended_cpc=metrics["blended_cpc"],
            blended_cpm=metrics["blended_cpm"],
            
            # Metadata
            calculation_method="bayesian",
            model_version="1.0",
        )
        
        self.session.add(roas_metrics)
        await self.session.commit()
        await self.session.refresh(roas_metrics)
        
        return roas_metrics
    
    async def _get_insights(
        self,
        campaign_id: Optional[UUID],
        adset_id: Optional[UUID],
        ad_id: Optional[UUID],
        date_start: datetime,
        date_end: datetime,
    ) -> List[MetaAdInsightsModel]:
        """Get insights for date range."""
        query = select(MetaAdInsightsModel).where(
            and_(
                MetaAdInsightsModel.date_start >= date_start,
                MetaAdInsightsModel.date_stop <= date_end,
            )
        )
        
        if ad_id:
            query = query.where(MetaAdInsightsModel.ad_id == ad_id)
        elif adset_id:
            query = query.where(MetaAdInsightsModel.adset_id == adset_id)
        elif campaign_id:
            query = query.where(MetaAdInsightsModel.campaign_id == campaign_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _get_outcomes(
        self,
        campaign_id: Optional[UUID],
        adset_id: Optional[UUID],
        ad_id: Optional[UUID],
        date_start: datetime,
        date_end: datetime,
    ) -> List[MetaPixelOutcomeModel]:
        """Get pixel outcomes for date range."""
        query = select(MetaPixelOutcomeModel).where(
            and_(
                MetaPixelOutcomeModel.event_timestamp >= date_start,
                MetaPixelOutcomeModel.event_timestamp <= date_end,
            )
        )
        
        if ad_id:
            query = query.where(MetaPixelOutcomeModel.ad_id == ad_id)
        elif adset_id:
            query = query.where(MetaPixelOutcomeModel.adset_id == adset_id)
        elif campaign_id:
            query = query.where(MetaPixelOutcomeModel.campaign_id == campaign_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _calculate_session_quality(
        self, outcomes: List[MetaPixelOutcomeModel]
    ) -> float:
        """
        Calculate session quality score (0-100).
        
        Based on:
        - Session duration
        - Pages visited
        - Bounce rate
        - Conversion events
        """
        if not outcomes:
            return 0.0
        
        # Average session duration (normalize to 0-100 scale)
        # Assume 300 seconds (5 minutes) is excellent
        avg_duration = sum(o.session_duration_seconds or 0 for o in outcomes) / len(outcomes)
        duration_score = min(avg_duration / 300 * 100, 100)
        
        # Conversion event quality
        # High-value events (Purchase, Lead) score higher
        high_value_events = sum(
            1 for o in outcomes
            if o.conversion_type in ["purchase", "lead", "complete_registration"]
        )
        conversion_score = (high_value_events / len(outcomes)) * 100
        
        # Weighted average
        quality_score = (duration_score * 0.6 + conversion_score * 0.4)
        
        return round(quality_score, 2)
    
    async def _calculate_retention_probability(
        self, outcomes: List[MetaPixelOutcomeModel]
    ) -> float:
        """
        Calculate user retention probability (0-1).
        
        Based on repeat conversions and session patterns.
        """
        if not outcomes:
            return 0.0
        
        # Count unique users (by session_id)
        unique_sessions = len(set(o.session_id for o in outcomes if o.session_id))
        
        if unique_sessions == 0:
            return 0.0
        
        # Calculate repeat conversion rate
        # More outcomes per session = higher retention
        repeat_rate = len(outcomes) / unique_sessions
        
        # Normalize to 0-1 (assume 3 conversions per session is excellent)
        retention_prob = min(repeat_rate / 3, 1.0)
        
        return round(retention_prob, 4)
    
    async def _estimate_lifetime_value(
        self, outcomes: List[MetaPixelOutcomeModel]
    ) -> float:
        """
        Estimate customer lifetime value.
        
        Simple model: average order value * estimated lifetime purchases
        """
        if not outcomes:
            return 0.0
        
        # Calculate average order value
        purchase_outcomes = [o for o in outcomes if o.conversion_type == "purchase"]
        
        if not purchase_outcomes:
            return 0.0
        
        avg_order_value = sum(o.value_usd or 0 for o in purchase_outcomes) / len(purchase_outcomes)
        
        # Estimate lifetime purchases (assume 5 purchases over customer lifetime)
        estimated_lifetime_purchases = 5.0
        
        ltv = avg_order_value * estimated_lifetime_purchases
        
        return round(ltv, 2)
    
    def _determine_performance_tier(
        self, actual_roas: float, conversion_rate: float
    ) -> str:
        """
        Determine performance tier based on ROAS and conversion rate.
        
        Tiers: excellent, good, average, poor, failing
        """
        if actual_roas >= 5.0 and conversion_rate >= 0.05:
            return "excellent"
        elif actual_roas >= 3.0 and conversion_rate >= 0.03:
            return "good"
        elif actual_roas >= 2.0 and conversion_rate >= 0.02:
            return "average"
        elif actual_roas >= 1.0 and conversion_rate >= 0.01:
            return "poor"
        else:
            return "failing"
    
    def _generate_recommendation(
        self,
        actual_roas: float,
        smoothed_roas: float,
        predicted_roas: float,
        performance_tier: str,
    ) -> tuple[str, Optional[float]]:
        """
        Generate optimization recommendation.
        
        Returns:
            Tuple of (recommendation, budget_change_percentage)
        """
        # Excellent performance: scale up
        if performance_tier == "excellent":
            return ("scale_up", 50.0)  # Increase budget by 50%
        
        # Good performance with positive trend: scale up moderately
        elif performance_tier == "good" and predicted_roas >= smoothed_roas:
            return ("scale_up", 25.0)  # Increase budget by 25%
        
        # Good performance but declining: monitor
        elif performance_tier == "good":
            return ("monitor", 0.0)
        
        # Average performance: test and optimize
        elif performance_tier == "average":
            return ("test", 0.0)
        
        # Poor performance: scale down
        elif performance_tier == "poor":
            return ("scale_down", -30.0)  # Decrease budget by 30%
        
        # Failing: pause
        else:
            return ("pause", -100.0)  # Pause ad
