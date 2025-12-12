"""
Unified Data Collector (PASO 10.16)

Aggregates data from multiple sources:
- Creative Analyzer (PASO 10.15)
- Insights Collector (PASO 10.7)
- ROAS Engine (PASO 10.5)
- Targeting Optimizer (PASO 10.12)
- Spike Manager (PASO 10.9)
"""
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID, uuid4
import random

from app.meta_creative_optimizer import schemas


class UnifiedDataCollector:
    """Collects and unifies data from all Meta Ads modules"""
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def collect_creative_data(
        self, creative_id: UUID, campaign_id: UUID
    ) -> schemas.UnifiedCreativeData:
        """
        Collect unified data for a single creative.
        
        In STUB mode: Generates synthetic data
        In LIVE mode: Queries all modules (10.5, 10.7, 10.9, 10.12, 10.15)
        """
        if self.mode == "stub":
            return await self._collect_stub_data(creative_id, campaign_id)
        else:
            # TODO LIVE: Query actual modules
            return await self._collect_live_data(creative_id, campaign_id)
    
    async def collect_campaign_data(
        self, campaign_id: UUID
    ) -> schemas.UnifiedCampaignData:
        """Collect unified data for entire campaign"""
        if self.mode == "stub":
            return await self._collect_campaign_stub_data(campaign_id)
        else:
            # TODO LIVE: Aggregate campaign-level data
            return await self._collect_campaign_live_data(campaign_id)
    
    async def collect_all_creatives(
        self, campaign_ids: Optional[List[UUID]] = None
    ) -> List[schemas.UnifiedCreativeData]:
        """Collect data for all creatives in specified campaigns"""
        if self.mode == "stub":
            # Generate 3-10 synthetic creatives per campaign
            all_creatives = []
            if campaign_ids is None:
                campaign_ids = [UUID('00000000-0000-0000-0000-000000000001')]
            
            for campaign_id in campaign_ids:
                num_creatives = random.randint(3, 10)
                for i in range(num_creatives):
                    creative_id = uuid4()  # Simple UUID generation
                    creative_data = await self.collect_creative_data(creative_id, campaign_id)
                    all_creatives.append(creative_data)
            
            return all_creatives
        else:
            # TODO LIVE: Query DB for all active creatives
            pass
    
    async def _collect_stub_data(
        self, creative_id: UUID, campaign_id: UUID
    ) -> schemas.UnifiedCreativeData:
        """Generate synthetic unified data (STUB mode)"""
        # Creative Analyzer data (PASO 10.15)
        overall_score = random.uniform(40, 95)
        is_fatigued = overall_score < 60 or random.random() < 0.2
        fatigue_score = random.uniform(50, 90) if is_fatigued else random.uniform(0, 30)
        
        # Insights data (PASO 10.7)
        ctr = random.uniform(0.5, 5.0)
        cvr = random.uniform(0.5, 8.0)
        cpc = random.uniform(0.5, 3.0)
        cpm = random.uniform(10, 40)
        roas = random.uniform(1.0, 6.0)
        impressions = random.randint(10000, 200000)
        clicks = int(impressions * ctr / 100)
        spend = clicks * cpc
        conversions = int(clicks * cvr / 100)
        
        # ROAS Engine data (PASO 10.5)
        roas_efficiency = min(100, roas * 15)
        roas_trend = random.choice(["improving", "stable", "declining"])
        
        # Targeting data (PASO 10.12)
        target_score = random.uniform(50, 95) if random.random() > 0.3 else None
        best_segments = ["25-34", "United States", "Mobile"] if target_score else None
        
        # Spike data (PASO 10.9)
        has_spike = random.random() < 0.1
        spike_severity = random.choice(["minor", "moderate"]) if has_spike else None
        
        return schemas.UnifiedCreativeData(
            creative_id=creative_id,
            campaign_id=campaign_id,
            # Creative Analyzer
            overall_score=overall_score,
            performance_score=min(40, overall_score * 0.4),
            engagement_score=min(30, overall_score * 0.3),
            is_fatigued=is_fatigued,
            fatigue_score=fatigue_score,
            fatigue_level="healthy" if fatigue_score < 30 else "moderate" if fatigue_score < 70 else "severe",
            # Insights
            ctr=ctr,
            cvr=cvr,
            cpc=cpc,
            cpm=cpm,
            roas=roas,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            spend=spend,
            # ROAS Engine
            roas_efficiency=roas_efficiency,
            roas_trend=roas_trend,
            # Targeting
            target_score=target_score,
            best_segments=best_segments,
            frequency_cap=random.uniform(3, 7) if target_score else None,
            # Spike
            has_spike=has_spike,
            spike_severity=spike_severity,
            # Metadata
            days_active=random.randint(3, 90),
            last_updated=datetime.utcnow(),
        )
    
    async def _collect_live_data(
        self, creative_id: UUID, campaign_id: UUID
    ) -> schemas.UnifiedCreativeData:
        """Collect real data from all modules (LIVE mode)"""
        # TODO LIVE: Implement real data collection
        # 1. Query MetaCreativeAnalysisModel (PASO 10.15)
        # 2. Query MetaInsightsCollector (PASO 10.7)
        # 3. Query ROASEngine results (PASO 10.5)
        # 4. Query TargetingOptimizer (PASO 10.12)
        # 5. Query SpikeManager (PASO 10.9)
        raise NotImplementedError("LIVE mode not implemented - use mode='stub'")
    
    async def _collect_campaign_stub_data(
        self, campaign_id: UUID
    ) -> schemas.UnifiedCampaignData:
        """Generate synthetic campaign data (STUB mode)"""
        total_creatives = random.randint(5, 15)
        active_creatives = random.randint(3, total_creatives)
        
        return schemas.UnifiedCampaignData(
            campaign_id=campaign_id,
            total_creatives=total_creatives,
            active_creatives=active_creatives,
            total_spend=random.uniform(5000, 50000),
            total_conversions=random.randint(100, 2000),
            avg_roas=random.uniform(2.0, 5.0),
            avg_ctr=random.uniform(1.5, 4.0),
            avg_cvr=random.uniform(2.0, 6.0),
            best_creative_id=UUID('00000000-0000-0000-0000-000000000001'),
            worst_creative_id=UUID('00000000-0000-0000-0000-000000000002'),
            collected_at=datetime.utcnow(),
        )
    
    async def _collect_campaign_live_data(
        self, campaign_id: UUID
    ) -> schemas.UnifiedCampaignData:
        """Collect real campaign data (LIVE mode)"""
        # TODO LIVE: Aggregate from DB
        raise NotImplementedError("LIVE mode not implemented - use mode='stub'")
