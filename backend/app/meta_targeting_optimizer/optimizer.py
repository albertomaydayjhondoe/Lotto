"""
Meta Targeting Optimizer - Main Orchestrator.

Integrates scoring, geo allocation, and audience building into
complete targeting recommendations.
"""
import uuid
import random
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.meta_targeting_optimizer.schemas import (
    TargetingRecommendation,
    GenderSplit,
    SegmentScore,
    SegmentMetrics,
    SegmentType,
)
from app.meta_targeting_optimizer.scoring_engine import BayesianScoringEngine
from app.meta_targeting_optimizer.geo_allocator import GeoAllocator
from app.meta_targeting_optimizer.audience_builder import AudienceBuilder
from app.meta_targeting_optimizer.models import (
    MetaTargetingRecommendationModel,
    MetaTargetingSegmentScoreModel,
)


class MetaTargetingOptimizer:
    """
    Main targeting optimizer orchestrator.
    
    Workflow:
    1. Load historical segment performance
    2. Score all segments (Bayesian smoothing)
    3. Allocate geo budget (España ≥35%)
    4. Build audiences (interests, behaviors, lookalikes)
    5. Generate targeting recommendations
    6. Persist to database
    """
    
    def __init__(self, db: AsyncSession, mode: str = "stub"):
        """
        Initialize optimizer.
        
        Args:
            db: Database session
            mode: "stub" or "live"
        """
        self.db = db
        self.mode = mode
        
        # Initialize engines
        self.scoring_engine = BayesianScoringEngine()
        self.geo_allocator = GeoAllocator()
        self.audience_builder = AudienceBuilder()
    
    async def run_optimization(
        self,
        campaign_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Run targeting optimization for campaign(s).
        
        Args:
            campaign_id: Single campaign or None for all active
            force_refresh: Force recomputation of segment scores
        
        Returns:
            Dict with run_id, recommendations count, duration
        """
        start_time = datetime.now()
        run_id = str(uuid.uuid4())
        
        # Step 1: Load segment scores (or compute if missing/force_refresh)
        segment_scores = await self._load_or_compute_segment_scores(force_refresh)
        
        # Step 2: Get campaigns to optimize
        if campaign_id:
            campaign_ids = [campaign_id]
        else:
            campaign_ids = await self._get_active_campaigns()
        
        # Step 3: Generate recommendations for each campaign
        recommendations = []
        for cid in campaign_ids:
            # Get adsets for campaign
            adsets = await self._get_campaign_adsets(cid)
            
            for adset in adsets:
                recommendation = await self._generate_recommendation(
                    run_id=run_id,
                    campaign_id=cid,
                    adset_id=adset["id"],
                    segment_scores=segment_scores
                )
                recommendations.append(recommendation)
        
        # Step 4: Persist recommendations
        await self._save_recommendations(recommendations)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "run_id": run_id,
            "recommendations_count": len(recommendations),
            "campaign_ids": campaign_ids,
            "duration_ms": duration_ms,
        }
    
    async def _load_or_compute_segment_scores(self, force_refresh: bool) -> List[SegmentScore]:
        """Load segment scores from DB or compute fresh."""
        if not force_refresh:
            # Try loading from DB
            result = await self.db.execute(
                select(MetaTargetingSegmentScoreModel)
                .where(MetaTargetingSegmentScoreModel.is_fatigued == False)
                .order_by(MetaTargetingSegmentScoreModel.composite_score.desc())
            )
            db_scores = result.scalars().all()
            
            if db_scores:
                # Convert to SegmentScore objects
                scores = []
                for db_score in db_scores:
                    metrics = SegmentMetrics(
                        impressions=db_score.impressions,
                        clicks=db_score.clicks,
                        conversions=db_score.conversions,
                        spend=db_score.spend,
                        revenue=db_score.revenue,
                        ctr=db_score.ctr,
                        cvr=db_score.cvr,
                        roas=db_score.roas,
                    )
                    
                    score = SegmentScore(
                        segment_id=db_score.segment_id,
                        segment_name=db_score.segment_name,
                        segment_type=SegmentType(db_score.segment_type),
                        metrics=metrics,
                        bayesian_ctr=db_score.bayesian_ctr,
                        bayesian_cvr=db_score.bayesian_cvr,
                        bayesian_roas=db_score.bayesian_roas,
                        composite_score=db_score.composite_score,
                        confidence=db_score.confidence,
                        rank=db_score.rank,
                        is_fatigued=db_score.is_fatigued,
                    )
                    scores.append(score)
                
                return scores
        
        # Compute fresh scores (STUB mode)
        return await self._compute_segment_scores_stub()
    
    async def _compute_segment_scores_stub(self) -> List[SegmentScore]:
        """Compute synthetic segment scores for stub mode."""
        scores = []
        
        # Generate synthetic interest scores
        for i in range(20):
            metrics = SegmentMetrics(
                impressions=random.randint(500, 10000),
                clicks=random.randint(10, 300),
                conversions=random.randint(1, 50),
                spend=random.uniform(50, 500),
                revenue=random.uniform(100, 1500),
            )
            
            score = self.scoring_engine.score_segment(
                metrics=metrics,
                segment_id=f"interest_{i}",
                segment_name=f"Interest {i}",
                segment_type=SegmentType.INTEREST
            )
            scores.append(score)
        
        # Generate synthetic behavior scores
        for i in range(10):
            metrics = SegmentMetrics(
                impressions=random.randint(500, 8000),
                clicks=random.randint(10, 250),
                conversions=random.randint(1, 40),
                spend=random.uniform(50, 400),
                revenue=random.uniform(100, 1200),
            )
            
            score = self.scoring_engine.score_segment(
                metrics=metrics,
                segment_id=f"behavior_{i}",
                segment_name=f"Behavior {i}",
                segment_type=SegmentType.BEHAVIOR
            )
            scores.append(score)
        
        # Rank all scores
        ranked = self.scoring_engine.rank_segments(scores)
        
        return ranked
    
    async def _get_active_campaigns(self) -> List[str]:
        """Get list of active campaign IDs (stub mode)."""
        # TODO: In live mode, query from MetaCampaignModel
        # result = await self.db.execute(
        #     select(MetaCampaignModel.campaign_id)
        #     .where(MetaCampaignModel.status == "ACTIVE")
        # )
        # return [r[0] for r in result.all()]
        
        # STUB: Return synthetic campaign IDs
        return [f"campaign_{i}" for i in range(1, 4)]
    
    async def _get_campaign_adsets(self, campaign_id: str) -> List[Dict]:
        """Get adsets for a campaign (stub mode)."""
        # TODO: In live mode, query from MetaAdSetModel
        # result = await self.db.execute(
        #     select(MetaAdSetModel)
        #     .where(MetaAdSetModel.campaign_id == campaign_id)
        #     .where(MetaAdSetModel.status == "ACTIVE")
        # )
        # return [{"id": r.adset_id} for r in result.scalars().all()]
        
        # STUB: Return synthetic adsets
        return [
            {"id": f"{campaign_id}_adset_1"},
            {"id": f"{campaign_id}_adset_2"},
        ]
    
    async def _generate_recommendation(
        self,
        run_id: str,
        campaign_id: str,
        adset_id: str,
        segment_scores: List[SegmentScore]
    ) -> TargetingRecommendation:
        """Generate targeting recommendation for an adset."""
        # Step 1: Geo allocation
        total_budget = random.uniform(100, 1000)  # STUB
        geo_performance = self.geo_allocator.get_default_geo_performance()
        geo_allocations = self.geo_allocator.allocate_budget(total_budget, geo_performance)
        
        countries = [g.country_code for g in geo_allocations]
        
        # Step 2: Interest targeting
        interests = self.audience_builder.build_interest_targeting(
            genre="action",  # TODO: Get from campaign metadata
            subgenre=None,
            interest_scores=segment_scores,
            max_interests=15
        )
        
        # Step 3: Behavior targeting
        behaviors = self.audience_builder.build_behavior_targeting(
            behavior_scores=segment_scores,
            max_behaviors=10
        )
        
        # Step 4: Custom audiences & Lookalikes (stub)
        custom_audiences = [
            self.audience_builder.generate_custom_audience_stub("converters", 5000),
            self.audience_builder.generate_custom_audience_stub("pixel_viewers", 15000),
        ]
        
        lookalikes = self.audience_builder.build_lookalike_audiences(
            custom_audiences=[ca.audience_id for ca in custom_audiences],
            countries=countries[:3],  # Top 3 countries
            max_lookalikes=2
        )
        
        # Step 5: Demographics (from historical data or defaults)
        age_min = 25
        age_max = 54
        gender = GenderSplit.ALL
        
        # Step 6: Frequency control
        frequency_cap = 3
        frequency_window_days = 7
        
        # Step 7: Budget per segment
        budget_per_segment = {}
        for geo in geo_allocations:
            budget_per_segment[geo.country_code] = geo.budget_amount
        
        # Step 8: Expected performance (weighted average of top segments)
        top_segments = segment_scores[:10]
        expected_ctr = sum(s.bayesian_ctr for s in top_segments) / len(top_segments) if top_segments else 0.015
        expected_cvr = sum(s.bayesian_cvr for s in top_segments) / len(top_segments) if top_segments else 0.020
        expected_roas = sum(s.bayesian_roas for s in top_segments) / len(top_segments) if top_segments else 2.5
        confidence = sum(s.confidence for s in top_segments) / len(top_segments) if top_segments else 0.5
        
        # Step 9: Reasoning trace
        reasoning = {
            "method": "bayesian_optimization",
            "geo_constraint": "ES_min_35pct",
            "top_interests_count": len(interests),
            "top_behaviors_count": len(behaviors),
            "lookalikes_generated": len(lookalikes),
            "total_budget": total_budget,
            "spain_allocation_pct": next((g.budget_pct for g in geo_allocations if g.country_code == "ES"), 0),
        }
        
        return TargetingRecommendation(
            adset_id=adset_id,
            campaign_id=campaign_id,
            countries=countries,
            geo_allocations=geo_allocations,
            age_min=age_min,
            age_max=age_max,
            gender=gender,
            interests=interests,
            behaviors=behaviors,
            custom_audiences=custom_audiences,
            lookalikes=lookalikes,
            frequency_cap=frequency_cap,
            frequency_window_days=frequency_window_days,
            total_budget=total_budget,
            budget_per_segment=budget_per_segment,
            reasoning=reasoning,
            expected_ctr=expected_ctr,
            expected_cvr=expected_cvr,
            expected_roas=expected_roas,
            confidence=confidence,
        )
    
    async def _save_recommendations(self, recommendations: List[TargetingRecommendation]):
        """Save recommendations to database."""
        for rec in recommendations:
            db_rec = MetaTargetingRecommendationModel(
                run_id=rec.reasoning.get("run_id", str(uuid.uuid4())),
                campaign_id=rec.campaign_id,
                adset_id=rec.adset_id,
                targeting_spec=rec.model_dump(),
                reasoning=rec.reasoning,
                expected_ctr=rec.expected_ctr,
                expected_cvr=rec.expected_cvr,
                expected_roas=rec.expected_roas,
                confidence=rec.confidence,
                status="pending",
            )
            self.db.add(db_rec)
        
        await self.db.commit()
    
    async def get_recommendation(self, campaign_id: str) -> Optional[TargetingRecommendation]:
        """Get latest recommendation for a campaign."""
        result = await self.db.execute(
            select(MetaTargetingRecommendationModel)
            .where(MetaTargetingRecommendationModel.campaign_id == campaign_id)
            .order_by(MetaTargetingRecommendationModel.created_at.desc())
            .limit(1)
        )
        db_rec = result.scalar_one_or_none()
        
        if not db_rec:
            return None
        
        return TargetingRecommendation(**db_rec.targeting_spec)
    
    async def apply_recommendation(self, recommendation_id: int, dry_run: bool = True) -> Dict:
        """Apply targeting recommendation to Meta API."""
        # Load recommendation
        result = await self.db.execute(
            select(MetaTargetingRecommendationModel)
            .where(MetaTargetingRecommendationModel.id == recommendation_id)
        )
        db_rec = result.scalar_one_or_none()
        
        if not db_rec:
            return {"success": False, "message": "Recommendation not found"}
        
        recommendation = TargetingRecommendation(**db_rec.targeting_spec)
        
        if dry_run or self.mode == "stub":
            # Simulate application
            applied_changes = {
                "countries": recommendation.countries,
                "age_range": f"{recommendation.age_min}-{recommendation.age_max}",
                "interests_count": len(recommendation.interests),
                "behaviors_count": len(recommendation.behaviors),
                "lookalikes_count": len(recommendation.lookalikes),
            }
            
            # Update status
            db_rec.status = "applied"
            db_rec.applied_at = datetime.now()
            await self.db.commit()
            
            return {
                "success": True,
                "recommendation_id": recommendation_id,
                "adset_id": recommendation.adset_id,
                "applied_changes": applied_changes,
                "message": "Applied in STUB mode (simulated)"
            }
        else:
            # TODO: Live mode - call Meta API
            # meta_client = MetaAdsClient(...)
            # response = await meta_client.update_adset_targeting(
            #     adset_id=recommendation.adset_id,
            #     targeting=recommendation.model_dump()
            # )
            
            return {
                "success": False,
                "message": "LIVE mode not implemented yet"
            }
