"""
ROAS Optimizer Module

Provides optimization recommendations for Meta Ads campaigns:
- Detect ads to scale up/down
- Identify winners and losers
- Compute budget reallocations
- Generate daily optimization plans
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    MetaROASMetricsModel,
    MetaCampaignModel,
    MetaAdsetModel,
    MetaAdModel,
)

logger = logging.getLogger(__name__)


class ROASOptimizer:
    """
    Optimize ad spend based on ROAS metrics.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Optimization thresholds
        self.scale_up_roas_threshold = 3.0  # ROAS > 3.0 = scale up
        self.scale_down_roas_threshold = 1.5  # ROAS < 1.5 = scale down
        self.pause_roas_threshold = 0.8  # ROAS < 0.8 = pause
        
        self.min_sample_size = 100  # Minimum impressions before optimization
        self.confidence_threshold = 0.6  # Minimum confidence score
        
    async def detect_ads_to_scale_up(
        self,
        campaign_id: UUID,
        lookback_days: int = 7,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Detect high-performing ads that should receive more budget.
        
        Criteria:
        - ROAS above threshold
        - High confidence score
        - Positive trend
        - Not outliers
        
        Args:
            campaign_id: Campaign UUID
            lookback_days: Days of data to analyze
            max_results: Maximum ads to return
            
        Returns:
            List of dicts with ad info and recommendations
        """
        date_start = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Query high-performing ads
        query = (
            select(MetaROASMetricsModel)
            .where(
                and_(
                    MetaROASMetricsModel.campaign_id == campaign_id,
                    MetaROASMetricsModel.date >= date_start,
                    MetaROASMetricsModel.actual_roas >= self.scale_up_roas_threshold,
                    MetaROASMetricsModel.confidence_score >= self.confidence_threshold,
                    MetaROASMetricsModel.is_outlier == 0,
                    MetaROASMetricsModel.sample_size >= self.min_sample_size,
                )
            )
            .order_by(desc(MetaROASMetricsModel.actual_roas))
            .limit(max_results)
        )
        
        result = await self.session.execute(query)
        metrics = result.scalars().all()
        
        recommendations = []
        
        for metric in metrics:
            # Get ad details
            ad = await self._get_ad(metric.ad_id)
            
            if not ad:
                continue
            
            # Calculate recommended budget increase
            budget_increase_pct = self._calculate_budget_increase(
                metric.actual_roas, metric.predicted_roas
            )
            
            recommendations.append({
                "ad_id": str(metric.ad_id),
                "ad_name": ad.ad_name if ad else "Unknown",
                "current_roas": metric.actual_roas,
                "predicted_roas": metric.predicted_roas,
                "confidence_score": metric.confidence_score,
                "performance_tier": metric.performance_tier,
                "recommendation": "scale_up",
                "budget_increase_pct": budget_increase_pct,
                "reason": f"High ROAS ({metric.actual_roas:.2f}x) with strong confidence",
            })
        
        return recommendations
    
    async def detect_ads_to_scale_down(
        self,
        campaign_id: UUID,
        lookback_days: int = 7,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Detect underperforming ads that should have budget reduced or paused.
        
        Criteria:
        - ROAS below threshold
        - Sufficient sample size to be confident
        - Consistent poor performance
        
        Args:
            campaign_id: Campaign UUID
            lookback_days: Days of data to analyze
            max_results: Maximum ads to return
            
        Returns:
            List of dicts with ad info and recommendations
        """
        date_start = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Query underperforming ads
        query = (
            select(MetaROASMetricsModel)
            .where(
                and_(
                    MetaROASMetricsModel.campaign_id == campaign_id,
                    MetaROASMetricsModel.date >= date_start,
                    MetaROASMetricsModel.actual_roas <= self.scale_down_roas_threshold,
                    MetaROASMetricsModel.sample_size >= self.min_sample_size,
                )
            )
            .order_by(MetaROASMetricsModel.actual_roas)
            .limit(max_results)
        )
        
        result = await self.session.execute(query)
        metrics = result.scalars().all()
        
        recommendations = []
        
        for metric in metrics:
            # Get ad details
            ad = await self._get_ad(metric.ad_id)
            
            if not ad:
                continue
            
            # Determine action: scale_down or pause
            if metric.actual_roas < self.pause_roas_threshold:
                action = "pause"
                budget_change_pct = -100.0
                reason = f"Very low ROAS ({metric.actual_roas:.2f}x) - not profitable"
            else:
                action = "scale_down"
                budget_change_pct = -30.0
                reason = f"Low ROAS ({metric.actual_roas:.2f}x) - reduce spend"
            
            recommendations.append({
                "ad_id": str(metric.ad_id),
                "ad_name": ad.ad_name if ad else "Unknown",
                "current_roas": metric.actual_roas,
                "predicted_roas": metric.predicted_roas,
                "confidence_score": metric.confidence_score,
                "performance_tier": metric.performance_tier,
                "recommendation": action,
                "budget_change_pct": budget_change_pct,
                "reason": reason,
            })
        
        return recommendations
    
    async def detect_winners_losers(
        self,
        campaign_id: UUID,
        lookback_days: int = 7,
    ) -> Dict:
        """
        Identify clear winners and losers in campaign.
        
        Args:
            campaign_id: Campaign UUID
            lookback_days: Days of data to analyze
            
        Returns:
            Dict with winners and losers lists
        """
        date_start = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get all ads with metrics
        query = (
            select(MetaROASMetricsModel)
            .where(
                and_(
                    MetaROASMetricsModel.campaign_id == campaign_id,
                    MetaROASMetricsModel.date >= date_start,
                    MetaROASMetricsModel.sample_size >= self.min_sample_size,
                )
            )
            .order_by(desc(MetaROASMetricsModel.actual_roas))
        )
        
        result = await self.session.execute(query)
        all_metrics = result.scalars().all()
        
        if not all_metrics:
            return {"winners": [], "losers": []}
        
        # Calculate median ROAS
        roas_values = [m.actual_roas for m in all_metrics if m.actual_roas is not None]
        median_roas = sorted(roas_values)[len(roas_values) // 2] if roas_values else 2.0
        
        winners = []
        losers = []
        
        for metric in all_metrics:
            ad = await self._get_ad(metric.ad_id)
            
            ad_info = {
                "ad_id": str(metric.ad_id),
                "ad_name": ad.ad_name if ad else "Unknown",
                "roas": metric.actual_roas,
                "revenue": metric.total_revenue_usd,
                "cost": metric.total_cost_usd,
                "conversions": metric.total_conversions,
                "performance_tier": metric.performance_tier,
            }
            
            # Winner: ROAS significantly above median
            if metric.actual_roas >= median_roas * 1.5:
                winners.append(ad_info)
            
            # Loser: ROAS significantly below median
            elif metric.actual_roas <= median_roas * 0.5:
                losers.append(ad_info)
        
        return {
            "winners": winners[:10],  # Top 10
            "losers": losers[:10],    # Bottom 10
            "median_roas": median_roas,
            "total_ads_analyzed": len(all_metrics),
        }
    
    async def compute_budget_reallocations(
        self,
        campaign_id: UUID,
        total_budget: float,
        lookback_days: int = 7,
    ) -> Dict:
        """
        Compute optimal budget allocation across ads.
        
        Uses proportional allocation based on ROAS and predicted performance.
        
        Args:
            campaign_id: Campaign UUID
            total_budget: Total daily budget to allocate
            lookback_days: Days of data to analyze
            
        Returns:
            Dict with budget allocations per ad
        """
        date_start = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get recent metrics for all ads
        query = (
            select(MetaROASMetricsModel)
            .where(
                and_(
                    MetaROASMetricsModel.campaign_id == campaign_id,
                    MetaROASMetricsModel.date >= date_start,
                )
            )
        )
        
        result = await self.session.execute(query)
        metrics = result.scalars().all()
        
        if not metrics:
            return {"allocations": [], "total_allocated": 0.0}
        
        # Calculate allocation weights based on ROAS and confidence
        allocations = []
        total_weight = 0.0
        
        for metric in metrics:
            # Skip outliers and low-confidence metrics
            if metric.is_outlier or (metric.confidence_score or 0) < self.confidence_threshold:
                continue
            
            # Weight = ROAS * confidence * (1 - is_paused)
            # Higher ROAS and confidence get more budget
            weight = (metric.actual_roas or 0) * (metric.confidence_score or 0.5)
            
            # Penalize underperformers
            if metric.actual_roas < self.pause_roas_threshold:
                weight = 0.0  # No budget for failing ads
            elif metric.actual_roas < self.scale_down_roas_threshold:
                weight *= 0.5  # Reduce budget for poor performers
            
            allocations.append({
                "ad_id": str(metric.ad_id),
                "current_roas": metric.actual_roas,
                "confidence": metric.confidence_score,
                "weight": weight,
            })
            
            total_weight += weight
        
        # Allocate budget proportionally
        if total_weight > 0:
            for alloc in allocations:
                alloc["allocated_budget"] = (alloc["weight"] / total_weight) * total_budget
                alloc["budget_share_pct"] = (alloc["weight"] / total_weight) * 100
        
        # Sort by allocated budget
        allocations.sort(key=lambda x: x["allocated_budget"], reverse=True)
        
        total_allocated = sum(a["allocated_budget"] for a in allocations)
        
        return {
            "allocations": allocations,
            "total_allocated": total_allocated,
            "total_budget": total_budget,
            "unallocated": total_budget - total_allocated,
        }
    
    async def compute_daily_optimization_plan(
        self,
        campaign_id: UUID,
        current_daily_budget: float,
    ) -> Dict:
        """
        Generate comprehensive daily optimization plan.
        
        Combines all optimization strategies:
        - Scale up recommendations
        - Scale down recommendations
        - Winner/loser identification
        - Budget reallocation
        
        Args:
            campaign_id: Campaign UUID
            current_daily_budget: Current daily budget
            
        Returns:
            Dict with complete optimization plan
        """
        # Get all recommendations
        scale_up = await self.detect_ads_to_scale_up(campaign_id)
        scale_down = await self.detect_ads_to_scale_down(campaign_id)
        winners_losers = await self.detect_winners_losers(campaign_id)
        budget_realloc = await self.compute_budget_reallocations(
            campaign_id, current_daily_budget
        )
        
        # Calculate total impact
        total_scale_up = len(scale_up)
        total_scale_down = len(scale_down)
        total_pause = len([r for r in scale_down if r["recommendation"] == "pause"])
        
        # Generate summary
        plan = {
            "campaign_id": str(campaign_id),
            "generated_at": datetime.utcnow().isoformat(),
            "current_daily_budget": current_daily_budget,
            
            # Recommendations
            "scale_up_recommendations": scale_up,
            "scale_down_recommendations": scale_down,
            
            # Winners and losers
            "winners": winners_losers["winners"],
            "losers": winners_losers["losers"],
            "median_roas": winners_losers.get("median_roas", 0.0),
            
            # Budget reallocation
            "budget_allocations": budget_realloc["allocations"],
            "total_allocated": budget_realloc["total_allocated"],
            "unallocated": budget_realloc.get("unallocated", 0.0),
            
            # Summary stats
            "summary": {
                "total_ads_to_scale_up": total_scale_up,
                "total_ads_to_scale_down": total_scale_down,
                "total_ads_to_pause": total_pause,
                "total_winners": len(winners_losers["winners"]),
                "total_losers": len(winners_losers["losers"]),
                "total_ads_analyzed": winners_losers.get("total_ads_analyzed", 0),
            },
            
            # Action items
            "action_items": self._generate_action_items(
                scale_up, scale_down, winners_losers
            ),
        }
        
        return plan
    
    def _calculate_budget_increase(
        self, actual_roas: float, predicted_roas: Optional[float]
    ) -> float:
        """
        Calculate recommended budget increase percentage.
        
        Higher ROAS = higher increase (up to 100%)
        """
        if actual_roas >= 5.0:
            return 100.0  # Double budget
        elif actual_roas >= 4.0:
            return 75.0
        elif actual_roas >= 3.5:
            return 50.0
        elif actual_roas >= 3.0:
            return 25.0
        else:
            return 10.0
    
    async def _get_ad(self, ad_id: Optional[UUID]) -> Optional[MetaAdModel]:
        """Get ad by ID."""
        if not ad_id:
            return None
        
        query = select(MetaAdModel).where(MetaAdModel.id == ad_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def _generate_action_items(
        self,
        scale_up: List[Dict],
        scale_down: List[Dict],
        winners_losers: Dict,
    ) -> List[str]:
        """Generate human-readable action items."""
        actions = []
        
        # Scale up actions
        if scale_up:
            actions.append(
                f"🚀 Increase budget for {len(scale_up)} high-performing ads"
            )
            for ad in scale_up[:3]:  # Top 3
                actions.append(
                    f"   • {ad['ad_name']}: +{ad['budget_increase_pct']:.0f}% "
                    f"(ROAS: {ad['current_roas']:.2f}x)"
                )
        
        # Scale down actions
        pause_ads = [a for a in scale_down if a["recommendation"] == "pause"]
        reduce_ads = [a for a in scale_down if a["recommendation"] == "scale_down"]
        
        if pause_ads:
            actions.append(f"⏸️  Pause {len(pause_ads)} underperforming ads")
            for ad in pause_ads[:3]:
                actions.append(
                    f"   • {ad['ad_name']}: PAUSE (ROAS: {ad['current_roas']:.2f}x)"
                )
        
        if reduce_ads:
            actions.append(f"⬇️  Reduce budget for {len(reduce_ads)} weak ads")
            for ad in reduce_ads[:3]:
                actions.append(
                    f"   • {ad['ad_name']}: {ad['budget_change_pct']:.0f}% "
                    f"(ROAS: {ad['current_roas']:.2f}x)"
                )
        
        # Winner celebration
        if winners_losers["winners"]:
            actions.append(
                f"🏆 {len(winners_losers['winners'])} winning ads identified"
            )
        
        return actions
