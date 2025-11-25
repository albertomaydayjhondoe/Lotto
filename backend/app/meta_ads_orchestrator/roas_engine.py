"""
ROAS Engine Core Module

Provides comprehensive ROAS calculation, prediction, and optimization capabilities.

Key Features:
- Real ROAS calculation from pixel outcomes
- Multi-touch attribution (last click, first click, linear, time decay)
- Bayesian smoothing for small sample sizes
- Outlier detection
- Conversion probability prediction
- Expected value calculations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from scipy import stats
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    MetaPixelOutcomeModel,
    MetaConversionEventModel,
    MetaROASMetricsModel,
    MetaAdInsightsModel,
    MetaAdModel,
    MetaAdsetModel,
    MetaCampaignModel,
)

logger = logging.getLogger(__name__)


class ROASCalculator:
    """
    Core ROAS calculation engine with statistical methods.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Configuration
        self.min_sample_size = 30  # Minimum conversions for reliable ROAS
        self.outlier_threshold = 3.0  # Z-score threshold for outliers
        self.bayesian_prior_weight = 0.2  # Weight of prior in Bayesian smoothing
        self.default_prior_roas = 2.0  # Default prior ROAS belief
        
    async def calculate_roas(
        self,
        campaign_id: Optional[UUID] = None,
        adset_id: Optional[UUID] = None,
        ad_id: Optional[UUID] = None,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate ROAS for given campaign/adset/ad.
        
        Args:
            campaign_id: Campaign UUID
            adset_id: Adset UUID  
            ad_id: Ad UUID
            date_start: Start date for calculation
            date_end: End date for calculation
            
        Returns:
            Dict with ROAS metrics and confidence intervals
        """
        # Default date range: last 7 days
        if not date_end:
            date_end = datetime.utcnow()
        if not date_start:
            date_start = date_end - timedelta(days=7)
        
        # Get conversion outcomes
        outcomes = await self._get_pixel_outcomes(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Get ad spend from insights
        spend = await self._get_ad_spend(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        
        # Calculate revenue
        total_revenue = sum(o.value_usd or 0.0 for o in outcomes)
        total_conversions = len(outcomes)
        
        # Calculate raw ROAS
        if spend > 0:
            raw_roas = total_revenue / spend
        else:
            raw_roas = 0.0
        
        # Apply Bayesian smoothing
        smoothed_roas = self._apply_bayesian_smoothing(
            raw_roas, total_conversions, spend
        )
        
        # Calculate confidence interval
        ci_low, ci_high = self._calculate_confidence_interval(
            outcomes, spend, total_conversions
        )
        
        # Detect outliers
        is_outlier, outlier_reason = self._detect_outlier(
            raw_roas, total_conversions, spend
        )
        
        # Calculate conversion rate
        clicks = await self._get_clicks(
            campaign_id, adset_id, ad_id, date_start, date_end
        )
        conversion_rate = total_conversions / clicks if clicks > 0 else 0.0
        
        return {
            "actual_roas": raw_roas,
            "smoothed_roas": smoothed_roas,
            "total_revenue_usd": total_revenue,
            "total_cost_usd": spend,
            "total_conversions": total_conversions,
            "conversion_rate": conversion_rate,
            "confidence_interval_low": ci_low,
            "confidence_interval_high": ci_high,
            "is_outlier": is_outlier,
            "outlier_reason": outlier_reason,
            "sample_size": total_conversions,
            "date_start": date_start,
            "date_end": date_end,
        }
    
    def _apply_bayesian_smoothing(
        self, observed_roas: float, conversions: int, spend: float
    ) -> float:
        """
        Apply Bayesian smoothing to ROAS to handle small sample sizes.
        
        Formula: posterior = (prior_weight * prior + data_weight * observed) / (prior_weight + data_weight)
        
        Args:
            observed_roas: Raw ROAS from data
            conversions: Number of conversions
            spend: Total ad spend
            
        Returns:
            Smoothed ROAS
        """
        if conversions == 0:
            return self.default_prior_roas
        
        # Calculate weight based on sample size
        # More conversions = more weight on observed data
        data_weight = min(conversions / self.min_sample_size, 1.0)
        prior_weight = self.bayesian_prior_weight * (1.0 - data_weight)
        
        # Weighted average
        smoothed = (
            prior_weight * self.default_prior_roas + data_weight * observed_roas
        ) / (prior_weight + data_weight)
        
        return smoothed
    
    def _calculate_confidence_interval(
        self, outcomes: List, spend: float, conversions: int, confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for ROAS using bootstrap.
        
        Args:
            outcomes: List of pixel outcomes
            spend: Total spend
            conversions: Number of conversions
            confidence: Confidence level (default 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if conversions < 3 or spend == 0:
            return (0.0, 0.0)
        
        # Extract conversion values
        values = [o.value_usd or 0.0 for o in outcomes]
        
        if len(values) == 0:
            return (0.0, 0.0)
        
        # Bootstrap resampling
        n_bootstrap = 1000
        roas_samples = []
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(values, size=len(values), replace=True)
            sample_revenue = np.sum(sample)
            sample_roas = sample_revenue / spend
            roas_samples.append(sample_roas)
        
        # Calculate percentiles
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_low = np.percentile(roas_samples, lower_percentile)
        ci_high = np.percentile(roas_samples, upper_percentile)
        
        return (float(ci_low), float(ci_high))
    
    def _detect_outlier(
        self, roas: float, conversions: int, spend: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect if ROAS is a statistical outlier.
        
        Args:
            roas: Calculated ROAS
            conversions: Number of conversions
            spend: Total spend
            
        Returns:
            Tuple of (is_outlier, reason)
        """
        # Check for extreme ROAS values
        if roas > 50:
            return (True, "Extremely high ROAS (>50x)")
        
        if roas < 0:
            return (True, "Negative ROAS")
        
        # Check for suspiciously low spend with high ROAS
        if spend < 10 and roas > 10:
            return (True, "Low spend (<$10) with high ROAS")
        
        # Check for very few conversions
        if conversions < 3 and roas > 5:
            return (True, f"Too few conversions ({conversions}) for reliable ROAS")
        
        return (False, None)
    
    async def _get_pixel_outcomes(
        self,
        campaign_id: Optional[UUID],
        adset_id: Optional[UUID],
        ad_id: Optional[UUID],
        date_start: datetime,
        date_end: datetime,
    ) -> List[MetaPixelOutcomeModel]:
        """Get pixel outcomes for given filters."""
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
    
    async def _get_ad_spend(
        self,
        campaign_id: Optional[UUID],
        adset_id: Optional[UUID],
        ad_id: Optional[UUID],
        date_start: datetime,
        date_end: datetime,
    ) -> float:
        """Get total ad spend from insights."""
        query = select(func.sum(MetaAdInsightsModel.spend)).where(
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
        spend = result.scalar()
        return float(spend) if spend else 0.0
    
    async def _get_clicks(
        self,
        campaign_id: Optional[UUID],
        adset_id: Optional[UUID],
        ad_id: Optional[UUID],
        date_start: datetime,
        date_end: datetime,
    ) -> int:
        """Get total clicks from insights."""
        query = select(func.sum(MetaAdInsightsModel.clicks)).where(
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
        clicks = result.scalar()
        return int(clicks) if clicks else 0


class AttributionEngine:
    """
    Multi-touch attribution for conversion events.
    """
    
    @staticmethod
    def apply_attribution(
        outcomes: List[MetaPixelOutcomeModel],
        model: str = "last_click"
    ) -> List[MetaPixelOutcomeModel]:
        """
        Apply attribution model to conversion outcomes.
        
        Args:
            outcomes: List of pixel outcomes
            model: Attribution model (last_click, first_click, linear, time_decay)
            
        Returns:
            List of outcomes with updated attribution_weight
        """
        if model == "last_click":
            # Last click gets 100% credit
            for outcome in outcomes:
                outcome.attribution_weight = 1.0
                outcome.attribution_model = "last_click"
        
        elif model == "first_click":
            # First click gets 100% credit
            for outcome in outcomes:
                outcome.attribution_weight = 1.0
                outcome.attribution_model = "first_click"
        
        elif model == "linear":
            # Equal credit to all touchpoints
            if len(outcomes) > 0:
                weight = 1.0 / len(outcomes)
                for outcome in outcomes:
                    outcome.attribution_weight = weight
                    outcome.attribution_model = "linear"
        
        elif model == "time_decay":
            # More recent touchpoints get more credit
            # Exponential decay with half-life of 7 days
            half_life_days = 7.0
            decay_constant = np.log(2) / half_life_days
            
            if len(outcomes) > 0:
                # Sort by timestamp
                sorted_outcomes = sorted(outcomes, key=lambda x: x.event_timestamp)
                latest_time = sorted_outcomes[-1].event_timestamp
                
                # Calculate weights
                weights = []
                for outcome in sorted_outcomes:
                    days_ago = (latest_time - outcome.event_timestamp).total_seconds() / 86400
                    weight = np.exp(-decay_constant * days_ago)
                    weights.append(weight)
                
                # Normalize weights to sum to 1
                total_weight = sum(weights)
                for i, outcome in enumerate(sorted_outcomes):
                    outcome.attribution_weight = weights[i] / total_weight
                    outcome.attribution_model = "time_decay"
        
        return outcomes


class PredictionEngine:
    """
    Predict future ROAS and conversion probability.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def predict_roas(
        self,
        campaign_id: Optional[UUID] = None,
        adset_id: Optional[UUID] = None,
        ad_id: Optional[UUID] = None,
        lookback_days: int = 30,
    ) -> Dict:
        """
        Predict future ROAS based on historical data.
        
        Simple prediction using exponential moving average.
        
        Args:
            campaign_id: Campaign UUID
            adset_id: Adset UUID
            ad_id: Ad UUID
            lookback_days: Days of historical data to use
            
        Returns:
            Dict with predicted ROAS and confidence
        """
        # Get historical ROAS metrics
        date_end = datetime.utcnow()
        date_start = date_end - timedelta(days=lookback_days)
        
        query = select(MetaROASMetricsModel).where(
            and_(
                MetaROASMetricsModel.date >= date_start,
                MetaROASMetricsModel.date <= date_end,
            )
        )
        
        if ad_id:
            query = query.where(MetaROASMetricsModel.ad_id == ad_id)
        elif adset_id:
            query = query.where(MetaROASMetricsModel.adset_id == adset_id)
        elif campaign_id:
            query = query.where(MetaROASMetricsModel.campaign_id == campaign_id)
        
        query = query.order_by(MetaROASMetricsModel.date.desc())
        
        result = await self.session.execute(query)
        historical_metrics = result.scalars().all()
        
        if not historical_metrics:
            return {
                "predicted_roas": 2.0,  # Default prior
                "confidence": 0.0,
                "historical_data_points": 0,
            }
        
        # Extract ROAS values
        roas_values = [
            m.actual_roas for m in historical_metrics
            if m.actual_roas is not None
        ]
        
        if not roas_values:
            return {
                "predicted_roas": 2.0,
                "confidence": 0.0,
                "historical_data_points": 0,
            }
        
        # Exponential moving average (more weight on recent data)
        alpha = 0.3  # Smoothing factor
        ema = roas_values[0]
        
        for roas in roas_values[1:]:
            ema = alpha * roas + (1 - alpha) * ema
        
        # Confidence based on amount of data
        confidence = min(len(roas_values) / 30, 1.0)
        
        return {
            "predicted_roas": ema,
            "confidence": confidence,
            "historical_data_points": len(roas_values),
            "recent_trend": "increasing" if roas_values[0] > roas_values[-1] else "decreasing",
        }
    
    def calculate_conversion_probability(
        self,
        clicks: int,
        conversions: int,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ) -> Dict:
        """
        Calculate conversion probability using Bayesian inference.
        
        Uses Beta distribution as conjugate prior for binomial likelihood.
        
        Args:
            clicks: Number of clicks
            conversions: Number of conversions
            prior_alpha: Prior alpha parameter (successes)
            prior_beta: Prior beta parameter (failures)
            
        Returns:
            Dict with probability and credible interval
        """
        if clicks == 0:
            return {
                "probability": 0.0,
                "credible_interval_low": 0.0,
                "credible_interval_high": 0.0,
            }
        
        # Posterior parameters
        posterior_alpha = prior_alpha + conversions
        posterior_beta = prior_beta + (clicks - conversions)
        
        # Mean of beta distribution
        probability = posterior_alpha / (posterior_alpha + posterior_beta)
        
        # 95% credible interval
        ci_low = stats.beta.ppf(0.025, posterior_alpha, posterior_beta)
        ci_high = stats.beta.ppf(0.975, posterior_alpha, posterior_beta)
        
        return {
            "probability": float(probability),
            "credible_interval_low": float(ci_low),
            "credible_interval_high": float(ci_high),
        }
    
    def calculate_expected_value(
        self,
        conversion_probability: float,
        average_order_value: float,
        cost_per_click: float,
    ) -> Dict:
        """
        Calculate expected value per click.
        
        EV = (conversion_prob * AOV) - CPC
        
        Args:
            conversion_probability: Probability of conversion
            average_order_value: Average order value
            cost_per_click: Cost per click
            
        Returns:
            Dict with expected value and metrics
        """
        expected_revenue = conversion_probability * average_order_value
        expected_value = expected_revenue - cost_per_click
        
        # Calculate break-even conversion rate
        breakeven_rate = cost_per_click / average_order_value if average_order_value > 0 else 0
        
        return {
            "expected_value": expected_value,
            "expected_revenue": expected_revenue,
            "expected_cost": cost_per_click,
            "breakeven_conversion_rate": breakeven_rate,
            "is_profitable": expected_value > 0,
        }
