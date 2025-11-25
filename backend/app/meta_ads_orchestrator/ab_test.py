"""
Meta Ads A/B Testing Module - PASO 10.4

Handles A/B test creation, evaluation, and winner selection.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from scipy import stats
import numpy as np

from app.models.database import (
    MetaAbTestModel,
    MetaCampaignModel,
    MetaAdModel,
    MetaAdInsightsModel,
    Clip,
    PublishLogModel,
    SocialAccountModel,
)

logger = logging.getLogger(__name__)


class ABTestEvaluator:
    """Evaluates A/B tests using statistical methods."""
    
    @staticmethod
    def chi_square_test(variant_a_data: Dict, variant_b_data: Dict) -> Dict[str, Any]:
        """
        Perform chi-square test on two variants.
        
        Args:
            variant_a_data: {"impressions": int, "clicks": int}
            variant_b_data: {"impressions": int, "clicks": int}
        
        Returns:
            {"chi2": float, "p_value": float, "significant": bool}
        """
        # Contingency table: [[clicks_a, non_clicks_a], [clicks_b, non_clicks_b]]
        clicks_a = variant_a_data.get("clicks", 0)
        impressions_a = variant_a_data.get("impressions", 1)
        non_clicks_a = impressions_a - clicks_a
        
        clicks_b = variant_b_data.get("clicks", 0)
        impressions_b = variant_b_data.get("impressions", 1)
        non_clicks_b = impressions_b - clicks_b
        
        contingency_table = np.array([
            [clicks_a, non_clicks_a],
            [clicks_b, non_clicks_b]
        ])
        
        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            significant = p_value < 0.05  # 95% confidence
            
            return {
                "chi2": float(chi2),
                "p_value": float(p_value),
                "significant": significant,
                "confidence": "95%",
            }
        except Exception as e:
            logger.error(f"Chi-square test failed: {e}")
            return {
                "chi2": 0.0,
                "p_value": 1.0,
                "significant": False,
                "error": str(e),
            }
    
    @staticmethod
    def calculate_ctr(impressions: int, clicks: int) -> float:
        """Calculate Click-Through Rate."""
        if impressions == 0:
            return 0.0
        return (clicks / impressions) * 100
    
    @staticmethod
    def calculate_cpc(spend: float, clicks: int) -> float:
        """Calculate Cost Per Click."""
        if clicks == 0:
            return 0.0
        return spend / clicks
    
    @staticmethod
    def calculate_roas(revenue: float, spend: float) -> float:
        """Calculate Return on Ad Spend."""
        if spend == 0:
            return 0.0
        return revenue / spend
    
    @staticmethod
    def calculate_engagement_rate(impressions: int, engagements: int) -> float:
        """Calculate engagement rate (likes + comments + shares / impressions)."""
        if impressions == 0:
            return 0.0
        return (engagements / impressions) * 100


async def create_ab_test(
    db: AsyncSession,
    campaign_id: UUID,
    test_name: str,
    variants: List[Dict[str, UUID]],
    metrics: List[str] = None,
    min_impressions: int = 1000,
    min_duration_hours: int = 48,
) -> MetaAbTestModel:
    """
    Create a new A/B test for a Meta Ads campaign.
    
    Args:
        db: Database session
        campaign_id: UUID of the Meta campaign
        test_name: Name for this A/B test
        variants: List of variants, e.g., [{"clip_id": uuid, "ad_id": uuid}, ...]
        metrics: Metrics to evaluate (default: ["ctr", "cpc", "engagement"])
        min_impressions: Minimum impressions before evaluation (default: 1000)
        min_duration_hours: Minimum test duration in hours (default: 48)
    
    Returns:
        Created MetaAbTestModel instance
    """
    if metrics is None:
        metrics = ["ctr", "cpc", "engagement"]
    
    # Validate campaign exists
    result = await db.execute(
        select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    
    # Validate variants
    if len(variants) < 2:
        raise ValueError("At least 2 variants required for A/B testing")
    
    # Create AB test
    ab_test = MetaAbTestModel(
        id=uuid4(),
        campaign_id=campaign_id,
        test_name=test_name,
        variants=variants,
        metrics=metrics,
        status="active",
        min_impressions=min_impressions,
        min_duration_hours=min_duration_hours,
        start_time=datetime.now(timezone.utc),
    )
    
    db.add(ab_test)
    await db.commit()
    await db.refresh(ab_test)
    
    logger.info(f"Created A/B test {ab_test.id} for campaign {campaign_id} with {len(variants)} variants")
    
    return ab_test


async def evaluate_ab_test(
    db: AsyncSession,
    ab_test_id: UUID,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate an A/B test and select a winner.
    
    Args:
        db: Database session
        ab_test_id: UUID of the A/B test
        force: Force evaluation even if embargo rules not met
    
    Returns:
        Evaluation result with winner information
    """
    # Load AB test
    result = await db.execute(
        select(MetaAbTestModel).where(MetaAbTestModel.id == ab_test_id)
    )
    ab_test = result.scalar_one_or_none()
    if not ab_test:
        raise ValueError(f"A/B test {ab_test_id} not found")
    
    if ab_test.status not in ["active", "needs_more_data"]:
        return {
            "success": False,
            "error": f"Cannot evaluate test with status: {ab_test.status}",
        }
    
    # Check embargo rules (minimum duration and impressions)
    test_duration_hours = (datetime.now(timezone.utc) - ab_test.start_time).total_seconds() / 3600
    
    if not force:
        if test_duration_hours < ab_test.min_duration_hours:
            ab_test.status = "needs_more_data"
            await db.commit()
            return {
                "success": False,
                "reason": "insufficient_duration",
                "message": f"Test running for {test_duration_hours:.1f}h, need {ab_test.min_duration_hours}h minimum",
            }
    
    # Gather metrics for each variant
    evaluator = ABTestEvaluator()
    variant_metrics = []
    
    for variant in ab_test.variants:
        ad_id = variant.get("ad_id")
        if not ad_id:
            continue
        
        # Get insights for this ad
        insights_result = await db.execute(
            select(MetaAdInsightsModel).where(
                MetaAdInsightsModel.ad_id == ad_id
            )
        )
        insights_list = insights_result.scalars().all()
        
        # Aggregate metrics
        total_impressions = sum(i.impressions or 0 for i in insights_list)
        total_clicks = sum(i.clicks or 0 for i in insights_list)
        total_spend = sum(i.spend or 0 for i in insights_list)
        total_conversions = sum(i.conversions or 0 for i in insights_list)
        total_purchase_value = sum(i.purchase_value or 0 for i in insights_list)
        
        # Calculate derived metrics
        ctr = evaluator.calculate_ctr(total_impressions, total_clicks)
        cpc = evaluator.calculate_cpc(total_spend, total_clicks)
        roas = evaluator.calculate_roas(total_purchase_value, total_spend)
        
        variant_metrics.append({
            "clip_id": variant.get("clip_id"),
            "ad_id": ad_id,
            "impressions": total_impressions,
            "clicks": total_clicks,
            "spend": total_spend,
            "conversions": total_conversions,
            "purchase_value": total_purchase_value,
            "ctr": ctr,
            "cpc": cpc,
            "roas": roas,
        })
    
    # Check minimum impressions
    if not force:
        max_impressions = max(v["impressions"] for v in variant_metrics) if variant_metrics else 0
        if max_impressions < ab_test.min_impressions:
            ab_test.status = "needs_more_data"
            await db.commit()
            return {
                "success": False,
                "reason": "insufficient_impressions",
                "message": f"Max impressions: {max_impressions}, need {ab_test.min_impressions} minimum",
            }
    
    # Perform statistical test (chi-square on CTR)
    if len(variant_metrics) >= 2:
        statistical_results = evaluator.chi_square_test(
            variant_metrics[0],
            variant_metrics[1]
        )
    else:
        statistical_results = {"significant": False, "error": "Not enough variants"}
    
    # Select winner based on composite score
    # Priority: ROAS > CTR > lower CPC
    def composite_score(v):
        roas_weight = 0.5
        ctr_weight = 0.3
        cpc_weight = 0.2
        
        # Normalize CPC (lower is better, so invert)
        max_cpc = max(vm["cpc"] for vm in variant_metrics) if variant_metrics else 1
        normalized_cpc = (max_cpc - v["cpc"]) / max_cpc if max_cpc > 0 else 0
        
        score = (
            v["roas"] * roas_weight +
            v["ctr"] * ctr_weight +
            normalized_cpc * cpc_weight
        )
        return score
    
    winner = max(variant_metrics, key=composite_score) if variant_metrics else None
    
    if not winner:
        return {
            "success": False,
            "error": "No winner could be determined",
        }
    
    # Update AB test with winner
    ab_test.winner_clip_id = UUID(winner["clip_id"]) if isinstance(winner["clip_id"], str) else winner["clip_id"]
    ab_test.winner_ad_id = UUID(winner["ad_id"]) if isinstance(winner["ad_id"], str) else winner["ad_id"]
    ab_test.winner_decided_at = datetime.now(timezone.utc)
    ab_test.status = "completed"
    ab_test.metrics_snapshot = variant_metrics
    ab_test.statistical_results = statistical_results
    ab_test.end_time = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(ab_test)
    
    logger.info(f"A/B test {ab_test_id} completed. Winner: {ab_test.winner_clip_id}")
    
    return {
        "success": True,
        "winner_clip_id": str(ab_test.winner_clip_id),
        "winner_ad_id": str(ab_test.winner_ad_id),
        "metrics_snapshot": variant_metrics,
        "statistical_results": statistical_results,
        "composite_scores": {v["clip_id"]: composite_score(v) for v in variant_metrics},
    }


async def archive_ab_test(db: AsyncSession, ab_test_id: UUID) -> MetaAbTestModel:
    """
    Archive an A/B test.
    
    Args:
        db: Database session
        ab_test_id: UUID of the A/B test
    
    Returns:
        Archived MetaAbTestModel instance
    """
    result = await db.execute(
        select(MetaAbTestModel).where(MetaAbTestModel.id == ab_test_id)
    )
    ab_test = result.scalar_one_or_none()
    if not ab_test:
        raise ValueError(f"A/B test {ab_test_id} not found")
    
    ab_test.status = "archived"
    ab_test.end_time = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(ab_test)
    
    logger.info(f"Archived A/B test {ab_test_id}")
    
    return ab_test


async def publish_winner(
    db: AsyncSession,
    ab_test_id: UUID,
    social_account_id: UUID,
) -> Dict[str, Any]:
    """
    Publish the winner of an A/B test to social media.
    
    Args:
        db: Database session
        ab_test_id: UUID of the A/B test
        social_account_id: UUID of the social account to publish to
    
    Returns:
        Result with publish log information
    """
    # Load AB test
    result = await db.execute(
        select(MetaAbTestModel).where(MetaAbTestModel.id == ab_test_id)
    )
    ab_test = result.scalar_one_or_none()
    if not ab_test:
        raise ValueError(f"A/B test {ab_test_id} not found")
    
    if ab_test.status != "completed":
        raise ValueError(f"Cannot publish from test with status: {ab_test.status}")
    
    if not ab_test.winner_clip_id:
        raise ValueError("No winner selected for this A/B test")
    
    # Check if already published
    if ab_test.published_to_social:
        return {
            "success": False,
            "error": "Winner already published",
            "publish_log_id": str(ab_test.publish_log_id) if ab_test.publish_log_id else None,
        }
    
    # Validate social account
    social_result = await db.execute(
        select(SocialAccountModel).where(SocialAccountModel.id == social_account_id)
    )
    social_account = social_result.scalar_one_or_none()
    if not social_account:
        raise ValueError(f"Social account {social_account_id} not found")
    
    # Create PublishLog
    publish_log = PublishLogModel(
        id=uuid4(),
        clip_id=ab_test.winner_clip_id,
        social_account_id=social_account_id,
        platform=social_account.platform,
        status="pending",  # Will be picked up by publishing queue
        schedule_type="immediate",
        scheduled_for=datetime.now(timezone.utc),  # Immediate
        scheduled_by="ab_test_winner",
        extra_metadata={
            "ab_test_id": str(ab_test.id),
            "source": "ab_test_winner",
            "winner_metrics": ab_test.metrics_snapshot,
            "caption": f"Winner of A/B test: {ab_test.test_name}",
        },
    )
    
    db.add(publish_log)
    await db.flush()
    
    # Update AB test
    ab_test.published_to_social = 1
    ab_test.publish_log_id = publish_log.id
    
    await db.commit()
    await db.refresh(publish_log)
    await db.refresh(ab_test)
    
    logger.info(f"Created publish log {publish_log.id} for A/B test winner {ab_test.winner_clip_id}")
    
    return {
        "success": True,
        "publish_log_id": str(publish_log.id),
        "clip_id": str(ab_test.winner_clip_id),
        "social_account_id": str(social_account_id),
        "status": "pending",
        "message": "Winner queued for publishing",
    }
