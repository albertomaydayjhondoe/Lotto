"""
Sprint 16: Influencer Trend Engine - Influencer Campaign Planner

Designs complete influencer campaigns with:
- Timeline (publication schedule)
- Assignments (trend variants per creator)
- Dependencies (coordination requirements)
- Expected outcomes (reach, engagement, virality)
- Risk map (temporal risk distribution)
- Satellite + ads synchronization

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from .influencer_selector import InfluencerPack, CreatorAssignment
from .trend_synthesis_engine import TrendBlueprint, TrendVariant, TrendVariantType


class PublicationPhase(Enum):
    """Campaign phases"""
    PREP = "prep"  # Preparation (creators prepare content)
    SEED = "seed"  # Initial seeding (primary creators post)
    AMPLIFY = "amplify"  # Amplification (support creators post)
    SUSTAIN = "sustain"  # Sustained momentum (satellites + organic)
    FINALE = "finale"  # Final push (ads + remaining creators)


@dataclass
class CreatorSchedule:
    """Publication schedule for a creator"""
    creator_username: str
    platform: str
    assigned_variant: TrendVariant
    publication_datetime: datetime
    phase: PublicationPhase
    dependencies: List[str]  # Usernames this depends on
    coordination_notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'creator_username': self.creator_username,
            'platform': self.platform,
            'assigned_variant_id': self.assigned_variant.variant_id,
            'publication_datetime': self.publication_datetime.isoformat(),
            'phase': self.phase.value,
            'dependencies': self.dependencies,
            'coordination_notes': self.coordination_notes
        }


@dataclass
class CampaignTimeline:
    """Complete campaign timeline"""
    campaign_start: datetime
    campaign_end: datetime
    prep_duration_hours: int
    schedules: List[CreatorSchedule]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'campaign_start': self.campaign_start.isoformat(),
            'campaign_end': self.campaign_end.isoformat(),
            'prep_duration_hours': self.prep_duration_hours,
            'total_duration_hours': int((self.campaign_end - self.campaign_start).total_seconds() / 3600),
            'schedules': [s.to_dict() for s in self.schedules]
        }
    
    def get_schedules_by_phase(self, phase: PublicationPhase) -> List[CreatorSchedule]:
        """Get all schedules for a specific phase"""
        return [s for s in self.schedules if s.phase == phase]


@dataclass
class ExpectedOutcomes:
    """Projected campaign outcomes"""
    phase_outcomes: Dict[str, Dict[str, int]]  # phase -> {impressions, engagement, reach}
    cumulative_impressions: int
    cumulative_engagement: int
    cumulative_reach: int
    peak_virality_datetime: datetime
    estimated_organic_multiplier: float  # How much organic content multiplies initial
    confidence_level: str  # "high", "medium", "low"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase_outcomes': self.phase_outcomes,
            'cumulative_impressions': self.cumulative_impressions,
            'cumulative_engagement': self.cumulative_engagement,
            'cumulative_reach': self.cumulative_reach,
            'peak_virality_datetime': self.peak_virality_datetime.isoformat(),
            'estimated_organic_multiplier': self.estimated_organic_multiplier,
            'confidence_level': self.confidence_level
        }


@dataclass
class RiskMap:
    """Temporal risk distribution across campaign"""
    risk_by_phase: Dict[str, float]  # phase -> risk score (0-1)
    high_risk_windows: List[Dict[str, Any]]  # [{start, end, reason}]
    mitigation_strategies: List[str]
    overall_risk_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_by_phase': self.risk_by_phase,
            'high_risk_windows': self.high_risk_windows,
            'mitigation_strategies': self.mitigation_strategies,
            'overall_risk_score': self.overall_risk_score
        }


@dataclass
class InfluencerCampaign:
    """
    Complete influencer campaign plan.
    
    Includes everything needed to execute:
    - Who posts what and when
    - How creators coordinate
    - Expected outcomes per phase
    - Risk assessment
    - Satellite + ads sync
    """
    campaign_id: str
    campaign_name: str
    pack: InfluencerPack
    blueprint: TrendBlueprint
    variants: List[TrendVariant]
    timeline: CampaignTimeline
    expected_outcomes: ExpectedOutcomes
    risk_map: RiskMap
    satellite_sync_schedule: List[Dict[str, Any]]  # When satellites should activate
    ads_schedule: List[Dict[str, Any]]  # When ads should run
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name,
            'pack': self.pack.to_dict(),
            'blueprint': self.blueprint.to_dict(),
            'variants': [v.to_dict() for v in self.variants],
            'timeline': self.timeline.to_dict(),
            'expected_outcomes': self.expected_outcomes.to_dict(),
            'risk_map': self.risk_map.to_dict(),
            'satellite_sync_schedule': self.satellite_sync_schedule,
            'ads_schedule': self.ads_schedule,
            'created_at': self.created_at.isoformat()
        }


class InfluencerCampaignPlanner:
    """
    Plans complete influencer campaigns.
    
    Strategy:
    1. Assign trend variants to creators based on role
    2. Build timeline with phases (seed → amplify → sustain → finale)
    3. Coordinate dependencies (support posts after primary)
    4. Sync satellites and ads for maximum impact
    5. Project outcomes per phase
    6. Map risks across timeline
    """
    
    def __init__(
        self,
        prep_duration_hours: int = 48,
        seed_duration_hours: int = 12,
        amplify_duration_hours: int = 24,
        sustain_duration_hours: int = 48,
        finale_duration_hours: int = 12
    ):
        """
        Initialize campaign planner.
        
        Args:
            *_duration_hours: Duration of each campaign phase
        """
        self.prep_duration = prep_duration_hours
        self.seed_duration = seed_duration_hours
        self.amplify_duration = amplify_duration_hours
        self.sustain_duration = sustain_duration_hours
        self.finale_duration = finale_duration_hours
    
    def plan_campaign(
        self,
        campaign_name: str,
        pack: InfluencerPack,
        blueprint: TrendBlueprint,
        variants: List[TrendVariant],
        start_datetime: Optional[datetime] = None
    ) -> InfluencerCampaign:
        """
        Create complete campaign plan.
        
        Args:
            campaign_name: Name for this campaign
            pack: Selected influencer pack
            blueprint: Trend blueprint
            variants: Trend variants
            start_datetime: When campaign starts (default: now + 2 days)
        
        Returns:
            InfluencerCampaign with full plan
        """
        if start_datetime is None:
            start_datetime = datetime.now() + timedelta(days=2)
        
        # Assign variants to creators
        assignments = self._assign_variants_to_creators(pack, variants)
        
        # Build timeline
        timeline = self._build_timeline(
            pack=pack,
            assignments=assignments,
            start_datetime=start_datetime
        )
        
        # Project outcomes
        outcomes = self._project_outcomes(pack, timeline, blueprint)
        
        # Map risks
        risk_map = self._map_risks(pack, timeline, blueprint)
        
        # Plan satellite sync
        satellite_schedule = self._plan_satellite_sync(pack, timeline)
        
        # Plan ads
        ads_schedule = self._plan_ads(pack, timeline, blueprint)
        
        # Generate campaign ID
        campaign_id = f"campaign_{campaign_name.replace(' ', '_').lower()}_{int(datetime.now().timestamp())}"
        
        return InfluencerCampaign(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            pack=pack,
            blueprint=blueprint,
            variants=variants,
            timeline=timeline,
            expected_outcomes=outcomes,
            risk_map=risk_map,
            satellite_sync_schedule=satellite_schedule,
            ads_schedule=ads_schedule
        )
    
    def _assign_variants_to_creators(
        self,
        pack: InfluencerPack,
        variants: List[TrendVariant]
    ) -> Dict[str, TrendVariant]:
        """Assign appropriate trend variants to each creator"""
        assignments = {}
        
        # Get variants by type
        influencer_variants = [v for v in variants if v.variant_type == TrendVariantType.INFLUENCER]
        satellite_variants = [v for v in variants if v.variant_type == TrendVariantType.SATELLITE]
        
        # Primary creators get influencer variants
        for creator in pack.primary_creators:
            if influencer_variants:
                assignments[creator.profile.raw_data.username] = influencer_variants[0]
        
        # Support creators get satellite variants (more authentic feel)
        for creator in pack.support_creators:
            if satellite_variants:
                assignments[creator.profile.raw_data.username] = satellite_variants[0]
        
        return assignments
    
    def _build_timeline(
        self,
        pack: InfluencerPack,
        assignments: Dict[str, TrendVariant],
        start_datetime: datetime
    ) -> CampaignTimeline:
        """Build publication timeline with phases"""
        schedules = []
        
        # Phase 1: SEED - Primary creators post first
        seed_start = start_datetime + timedelta(hours=self.prep_duration)
        
        for i, creator in enumerate(pack.primary_creators):
            username = creator.profile.raw_data.username
            platform = creator.profile.raw_data.platform.value
            
            # Stagger posts (2-4 hours apart)
            post_time = seed_start + timedelta(hours=i * 3)
            
            schedule = CreatorSchedule(
                creator_username=username,
                platform=platform,
                assigned_variant=assignments[username],
                publication_datetime=post_time,
                phase=PublicationPhase.SEED,
                dependencies=[],
                coordination_notes="Primary driver - post at optimal time for your audience"
            )
            
            schedules.append(schedule)
        
        # Phase 2: AMPLIFY - Support creators post after primaries
        amplify_start = seed_start + timedelta(hours=self.seed_duration)
        
        for i, creator in enumerate(pack.support_creators):
            username = creator.profile.raw_data.username
            platform = creator.profile.raw_data.platform.value
            
            # Stagger posts (1-2 hours apart)
            post_time = amplify_start + timedelta(hours=i * 1.5)
            
            # Depend on at least one primary creator
            dependencies = [pack.primary_creators[0].profile.raw_data.username]
            
            schedule = CreatorSchedule(
                creator_username=username,
                platform=platform,
                assigned_variant=assignments[username],
                publication_datetime=post_time,
                phase=PublicationPhase.AMPLIFY,
                dependencies=dependencies,
                coordination_notes="Support amplifier - reference primary creator's post if possible"
            )
            
            schedules.append(schedule)
        
        # Calculate campaign end
        campaign_end = amplify_start + timedelta(
            hours=self.amplify_duration + self.sustain_duration + self.finale_duration
        )
        
        return CampaignTimeline(
            campaign_start=start_datetime,
            campaign_end=campaign_end,
            prep_duration_hours=self.prep_duration,
            schedules=schedules
        )
    
    def _project_outcomes(
        self,
        pack: InfluencerPack,
        timeline: CampaignTimeline,
        blueprint: TrendBlueprint
    ) -> ExpectedOutcomes:
        """Project expected outcomes per phase"""
        
        # Base impressions/engagement from pack
        base_impressions = pack.total_expected_impressions
        base_engagement = pack.total_expected_engagement
        
        # Phase multipliers (how outcomes build over time)
        phase_multipliers = {
            PublicationPhase.SEED: 0.3,  # 30% of total in seed
            PublicationPhase.AMPLIFY: 0.4,  # 40% in amplify
            PublicationPhase.SUSTAIN: 0.2,  # 20% in sustain (organic takeover)
            PublicationPhase.FINALE: 0.1  # 10% in finale
        }
        
        # Virality boost from blueprint
        virality_boost = blueprint.virality_potential
        
        # Calculate phase outcomes
        phase_outcomes = {}
        
        for phase, multiplier in phase_multipliers.items():
            phase_impressions = int(base_impressions * multiplier * (1 + virality_boost))
            phase_engagement = int(base_engagement * multiplier * (1 + virality_boost))
            phase_reach = int(phase_impressions * 0.7)  # 70% of impressions = unique reach
            
            phase_outcomes[phase.value] = {
                'impressions': phase_impressions,
                'engagement': phase_engagement,
                'reach': phase_reach
            }
        
        # Cumulative totals
        cumulative_impressions = sum(p['impressions'] for p in phase_outcomes.values())
        cumulative_engagement = sum(p['engagement'] for p in phase_outcomes.values())
        cumulative_reach = sum(p['reach'] for p in phase_outcomes.values())
        
        # Peak virality occurs during AMPLIFY phase
        peak_time = timeline.campaign_start + timedelta(
            hours=self.prep_duration + self.seed_duration + (self.amplify_duration / 2)
        )
        
        # Organic multiplier (how much organic content adds)
        organic_multiplier = 1.0 + (virality_boost * 2)  # High virality = more organic
        
        # Confidence level based on pack quality
        avg_composite = sum(
            c.profile.scores.composite_score() for c in pack.all_creators
        ) / len(pack.all_creators)
        
        if avg_composite > 0.7:
            confidence = "high"
        elif avg_composite > 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        return ExpectedOutcomes(
            phase_outcomes=phase_outcomes,
            cumulative_impressions=cumulative_impressions,
            cumulative_engagement=cumulative_engagement,
            cumulative_reach=cumulative_reach,
            peak_virality_datetime=peak_time,
            estimated_organic_multiplier=round(organic_multiplier, 2),
            confidence_level=confidence
        )
    
    def _map_risks(
        self,
        pack: InfluencerPack,
        timeline: CampaignTimeline,
        blueprint: TrendBlueprint
    ) -> RiskMap:
        """Map risks across campaign timeline"""
        
        # Risk by phase
        risk_by_phase = {
            PublicationPhase.SEED.value: pack.max_risk_score * 0.8,  # Highest risk in seed
            PublicationPhase.AMPLIFY.value: pack.max_risk_score * 0.6,
            PublicationPhase.SUSTAIN.value: pack.max_risk_score * 0.4,
            PublicationPhase.FINALE.value: pack.max_risk_score * 0.3
        }
        
        # Add blueprint risk
        trend_risk = blueprint.risk_score
        for phase in risk_by_phase:
            risk_by_phase[phase] = min(1.0, risk_by_phase[phase] + trend_risk * 0.5)
        
        # Identify high-risk windows (risk > 0.5)
        high_risk_windows = []
        
        for phase, risk in risk_by_phase.items():
            if risk > 0.5:
                # Find phase schedules
                phase_enum = PublicationPhase(phase)
                phase_schedules = timeline.get_schedules_by_phase(phase_enum)
                
                if phase_schedules:
                    start = min(s.publication_datetime for s in phase_schedules)
                    end = max(s.publication_datetime for s in phase_schedules) + timedelta(hours=24)
                    
                    high_risk_windows.append({
                        'start': start.isoformat(),
                        'end': end.isoformat(),
                        'phase': phase,
                        'risk_score': round(risk, 2),
                        'reason': f"High-risk creators active in {phase} phase"
                    })
        
        # Mitigation strategies
        mitigation = []
        
        if pack.max_risk_score > 0.4:
            mitigation.append("Monitor creator posts closely during seed phase")
        
        if trend_risk > 0.3:
            mitigation.append("Review trend content before creator publication")
        
        if len(high_risk_windows) > 0:
            mitigation.append("Prepare crisis response plan for high-risk windows")
        
        mitigation.append("Integrate with Cognitive Governance (Sprint 14) for real-time monitoring")
        mitigation.append("Enforce Decision Policies (Sprint 15) before each phase")
        
        # Overall risk
        overall_risk = max(risk_by_phase.values())
        
        return RiskMap(
            risk_by_phase=risk_by_phase,
            high_risk_windows=high_risk_windows,
            mitigation_strategies=mitigation,
            overall_risk_score=round(overall_risk, 2)
        )
    
    def _plan_satellite_sync(
        self,
        pack: InfluencerPack,
        timeline: CampaignTimeline
    ) -> List[Dict[str, Any]]:
        """Plan when satellites should activate"""
        schedule = []
        
        # Satellites activate during SUSTAIN phase
        sustain_start = timeline.campaign_start + timedelta(
            hours=self.prep_duration + self.seed_duration + self.amplify_duration
        )
        
        # Stagger satellite activation (waves of 5-10 satellites)
        satellites_per_wave = 5
        total_waves = (pack.satellite_sync_count + satellites_per_wave - 1) // satellites_per_wave
        
        for wave in range(total_waves):
            activation_time = sustain_start + timedelta(hours=wave * 6)
            
            schedule.append({
                'wave': wave + 1,
                'activation_datetime': activation_time.isoformat(),
                'satellite_count': min(satellites_per_wave, pack.satellite_sync_count - wave * satellites_per_wave),
                'action': 'Post organic content with trend variant',
                'coordination': f'Reference influencer content from {pack.primary_creators[0].profile.raw_data.username}'
            })
        
        return schedule
    
    def _plan_ads(
        self,
        pack: InfluencerPack,
        timeline: CampaignTimeline,
        blueprint: TrendBlueprint
    ) -> List[Dict[str, Any]]:
        """Plan when ads should run"""
        schedule = []
        
        # Ads start during AMPLIFY phase (ride the momentum)
        ads_start = timeline.campaign_start + timedelta(
            hours=self.prep_duration + self.seed_duration + (self.amplify_duration / 2)
        )
        
        # Ads run through FINALE
        ads_end = timeline.campaign_end
        
        schedule.append({
            'campaign_phase': 'amplify_to_finale',
            'start_datetime': ads_start.isoformat(),
            'end_datetime': ads_end.isoformat(),
            'budget_allocation': pack.total_budget_usd * 0.3,  # 30% of total budget to ads
            'target_audience': 'Lookalike audiences based on influencer followers',
            'creative': f'Use {blueprint.visual_style.value} style with {blueprint.sound_cut_timestamp} sound cut',
            'optimization': 'Optimize for video views and engagement'
        })
        
        return schedule


if __name__ == "__main__":
    # Example usage
    from .influencer_scraper import InfluencerScraper
    from .influencer_analysis import InfluencerAnalyzer
    from .influencer_selector import InfluencerSelector
    from .trend_synthesis_engine import TrendSynthesisEngine
    
    # Full pipeline
    scraper = InfluencerScraper()
    analyzer = InfluencerAnalyzer()
    selector = InfluencerSelector()
    trend_engine = TrendSynthesisEngine()
    planner = InfluencerCampaignPlanner()
    
    # 1. Scrape creators
    urls = [f"https://www.tiktok.com/@creator{i}" for i in range(1, 9)]
    raw_data = scraper.scrape_multiple(urls)
    
    # 2. Analyze
    profiles = analyzer.analyze_batch(raw_data)
    
    # 3. Select pack
    pack = selector.select_optimal_pack(profiles, budget_usd=5000.0)
    
    # 4. Synthesize trend
    blueprint, variants = trend_engine.synthesize_trend(
        song_name="Bailando en la Noche",
        song_tempo=128,
        song_mood="energetic",
        visual_aesthetic="urban raw"
    )
    
    # 5. Plan campaign
    if pack:
        campaign = planner.plan_campaign(
            campaign_name="Bailando Launch",
            pack=pack,
            blueprint=blueprint,
            variants=variants
        )
        
        print("✓ Campaign planned successfully")
        print(f"\n  Campaign: {campaign.campaign_name}")
        print(f"  ID: {campaign.campaign_id}")
        print(f"  Creators: {pack.total_creators}")
        print(f"  Budget: ${pack.total_budget_usd:,.2f}")
        print(f"  Duration: {(campaign.timeline.campaign_end - campaign.timeline.campaign_start).days} days")
        print(f"  Expected impressions: {campaign.expected_outcomes.cumulative_impressions:,}")
        print(f"  Expected engagement: {campaign.expected_outcomes.cumulative_engagement:,}")
        print(f"  Overall risk: {campaign.risk_map.overall_risk_score:.2f}")
        print(f"  Confidence: {campaign.expected_outcomes.confidence_level}")
        print(f"  Satellite waves: {len(campaign.satellite_sync_schedule)}")
    else:
        print("❌ Failed to create pack")
