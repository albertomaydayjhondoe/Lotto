"""
Sprint 16: Influencer Trend Engine - Influencer Selector

Optimal influencer selection using constraint-based optimization.

Optimization Problem:
    maximize: impact * cultural_fit * trend_reactivity
    subject to:
        - total_budget <= user_budget
        - max_risk < risk_threshold (default: 0.45)
        - diversity >= diversity_threshold (default: 0.6)
        - min_creators <= count <= max_creators

Features:
- Multi-objective optimization
- Budget allocation
- Diversity enforcement
- Risk management
- Primary/support creator classification

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import math

from .influencer_analysis import InfluencerProfile, InfluencerScores


@dataclass
class CreatorAssignment:
    """Assignment of creator to campaign role"""
    profile: InfluencerProfile
    role: str  # "primary", "support"
    allocated_budget_usd: float
    expected_impressions: int
    expected_engagement: int
    priority: int  # 1 = highest, 2 = second, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.profile.raw_data.username,
            'platform': self.profile.raw_data.platform.value,
            'role': self.role,
            'allocated_budget_usd': self.allocated_budget_usd,
            'expected_impressions': self.expected_impressions,
            'expected_engagement': self.expected_engagement,
            'priority': self.priority,
            'scores': self.profile.scores.to_dict()
        }


@dataclass
class InfluencerPack:
    """
    Optimized pack of influencers for a campaign.
    
    Contains:
    - Primary creators (main drivers)
    - Support creators (amplifiers)
    - Budget distribution
    - Expected outcomes
    """
    pack_id: str
    primary_creators: List[CreatorAssignment]
    support_creators: List[CreatorAssignment]
    total_budget_usd: float
    total_expected_impressions: int
    total_expected_engagement: int
    average_cpm: float
    diversity_score: float
    max_risk_score: float
    satellite_sync_count: int  # Recommended satellite accounts to sync
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pack_id': self.pack_id,
            'primary_creators': [c.to_dict() for c in self.primary_creators],
            'support_creators': [c.to_dict() for c in self.support_creators],
            'total_budget_usd': self.total_budget_usd,
            'total_expected_impressions': self.total_expected_impressions,
            'total_expected_engagement': self.total_expected_engagement,
            'average_cpm': self.average_cpm,
            'diversity_score': self.diversity_score,
            'max_risk_score': self.max_risk_score,
            'satellite_sync_count': self.satellite_sync_count,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def all_creators(self) -> List[CreatorAssignment]:
        """Get all creators (primary + support)"""
        return self.primary_creators + self.support_creators
    
    @property
    def total_creators(self) -> int:
        """Total number of creators"""
        return len(self.primary_creators) + len(self.support_creators)


class InfluencerSelector:
    """
    Selects optimal influencers under budget and risk constraints.
    
    Uses greedy optimization with smart heuristics:
    1. Sort candidates by composite score
    2. Select primary creators (high impact + cultural fit)
    3. Select support creators (fast reactivity + cost-effective)
    4. Enforce diversity (platforms, topics, follower tiers)
    5. Respect budget and risk limits
    """
    
    def __init__(
        self,
        risk_threshold: float = 0.45,
        diversity_threshold: float = 0.6,
        min_primary_creators: int = 2,
        max_primary_creators: int = 5,
        min_support_creators: int = 3,
        max_support_creators: int = 8
    ):
        """
        Initialize selector.
        
        Args:
            risk_threshold: Maximum acceptable risk (0-1)
            diversity_threshold: Minimum diversity score (0-1)
            min/max_primary_creators: Range for primary creators
            min/max_support_creators: Range for support creators
        """
        self.risk_threshold = risk_threshold
        self.diversity_threshold = diversity_threshold
        self.min_primary = min_primary_creators
        self.max_primary = max_primary_creators
        self.min_support = min_support_creators
        self.max_support = max_support_creators
    
    def select_optimal_pack(
        self,
        candidates: List[InfluencerProfile],
        budget_usd: float,
        campaign_goals: Optional[Dict[str, Any]] = None
    ) -> Optional[InfluencerPack]:
        """
        Select optimal influencer pack.
        
        Args:
            candidates: List of analyzed influencer profiles
            budget_usd: Total available budget
            campaign_goals: Optional goals (impressions, engagement, etc.)
        
        Returns:
            InfluencerPack or None if no valid pack found
        """
        if not candidates:
            print("No candidates provided")
            return None
        
        if budget_usd <= 0:
            print("Invalid budget")
            return None
        
        # Filter out high-risk candidates
        safe_candidates = [
            c for c in candidates
            if c.scores.risk_score < self.risk_threshold
        ]
        
        if len(safe_candidates) < (self.min_primary + self.min_support):
            print(f"Not enough safe candidates (need {self.min_primary + self.min_support}, have {len(safe_candidates)})")
            return None
        
        # Sort by composite score (descending)
        sorted_candidates = sorted(
            safe_candidates,
            key=lambda c: c.scores.composite_score(),
            reverse=True
        )
        
        # Select primary creators (high impact + cultural fit)
        primary_pool = [
            c for c in sorted_candidates
            if c.scores.impact_score >= 0.3 and c.scores.cultural_fit >= 0.3
        ]
        
        # Select support creators (fast reactivity + cost-effective)
        support_pool = [
            c for c in sorted_candidates
            if c.scores.trend_reactivity >= 0.4 and c.scores.price_efficiency >= 0.2
        ]
        
        # Build pack
        pack = self._build_pack(
            primary_pool=primary_pool,
            support_pool=support_pool,
            budget=budget_usd,
            goals=campaign_goals
        )
        
        return pack
    
    def _build_pack(
        self,
        primary_pool: List[InfluencerProfile],
        support_pool: List[InfluencerProfile],
        budget: float,
        goals: Optional[Dict[str, Any]]
    ) -> Optional[InfluencerPack]:
        """Build influencer pack from pools"""
        
        # Allocate budget (70% primary, 30% support)
        primary_budget = budget * 0.70
        support_budget = budget * 0.30
        
        # Select primary creators
        primary_creators = self._select_creators(
            pool=primary_pool,
            budget=primary_budget,
            role="primary",
            min_count=self.min_primary,
            max_count=self.max_primary
        )
        
        if not primary_creators or len(primary_creators) < self.min_primary:
            print("Failed to select enough primary creators")
            return None
        
        # Select support creators
        support_creators = self._select_creators(
            pool=support_pool,
            budget=support_budget,
            role="support",
            min_count=self.min_support,
            max_count=self.max_support
        )
        
        if not support_creators or len(support_creators) < self.min_support:
            print("Failed to select enough support creators")
            return None
        
        # Check diversity
        all_selected = [c.profile for c in primary_creators + support_creators]
        diversity = self._calculate_diversity(all_selected)
        
        if diversity < self.diversity_threshold:
            print(f"Diversity too low: {diversity:.2f} < {self.diversity_threshold}")
            return None
        
        # Calculate totals
        total_budget = sum(c.allocated_budget_usd for c in primary_creators + support_creators)
        total_impressions = sum(c.expected_impressions for c in primary_creators + support_creators)
        total_engagement = sum(c.expected_engagement for c in primary_creators + support_creators)
        
        avg_cpm = (total_budget / total_impressions * 1000) if total_impressions > 0 else 0
        
        # Max risk across all creators
        max_risk = max(c.profile.scores.risk_score for c in primary_creators + support_creators)
        
        # Recommended satellite sync count (1 satellite per 10k expected impressions)
        satellite_sync = max(5, int(total_impressions / 10000))
        
        # Generate pack ID
        pack_id = f"pack_{int(datetime.now().timestamp())}"
        
        return InfluencerPack(
            pack_id=pack_id,
            primary_creators=primary_creators,
            support_creators=support_creators,
            total_budget_usd=round(total_budget, 2),
            total_expected_impressions=total_impressions,
            total_expected_engagement=total_engagement,
            average_cpm=round(avg_cpm, 2),
            diversity_score=round(diversity, 2),
            max_risk_score=round(max_risk, 2),
            satellite_sync_count=satellite_sync
        )
    
    def _select_creators(
        self,
        pool: List[InfluencerProfile],
        budget: float,
        role: str,
        min_count: int,
        max_count: int
    ) -> List[CreatorAssignment]:
        """
        Select creators from pool within budget.
        
        Greedy algorithm: pick best candidates until budget exhausted.
        """
        selected = []
        remaining_budget = budget
        
        # Sort by composite score
        sorted_pool = sorted(
            pool,
            key=lambda c: c.scores.composite_score(),
            reverse=True
        )
        
        for i, profile in enumerate(sorted_pool):
            if len(selected) >= max_count:
                break
            
            # Estimate cost for this creator
            # Budget per creator = (avg_views * CPM / 1000)
            estimated_cost = profile.raw_data.metrics.avg_views * profile.estimated_cpm_usd / 1000
            
            # Check if we can afford
            if estimated_cost > remaining_budget:
                # If we haven't met minimum, try cheaper options
                if len(selected) < min_count:
                    continue
                else:
                    break
            
            # Calculate expected outcomes
            expected_impressions = int(profile.raw_data.metrics.avg_views)
            expected_engagement = int(
                expected_impressions * profile.raw_data.metrics.engagement_rate
            )
            
            # Create assignment
            assignment = CreatorAssignment(
                profile=profile,
                role=role,
                allocated_budget_usd=round(estimated_cost, 2),
                expected_impressions=expected_impressions,
                expected_engagement=expected_engagement,
                priority=i + 1
            )
            
            selected.append(assignment)
            remaining_budget -= estimated_cost
        
        # Check if minimum met
        if len(selected) < min_count:
            return []
        
        return selected
    
    def _calculate_diversity(self, profiles: List[InfluencerProfile]) -> float:
        """
        Calculate diversity score (0-1).
        
        Diversity dimensions:
        - Platform mix
        - Follower tier mix
        - Topic diversity
        """
        if not profiles:
            return 0.0
        
        # Platform diversity
        platforms = set(p.raw_data.platform for p in profiles)
        platform_diversity = len(platforms) / 3.0  # Max 3 platforms (TikTok, IG, YT)
        
        # Follower tier diversity
        tiers = set(self._get_follower_tier(p) for p in profiles)
        tier_diversity = len(tiers) / 4.0  # Max 4 tiers (micro, mid, macro, mega)
        
        # Topic diversity (unique topics across all creators)
        all_topics = set()
        for p in profiles:
            all_topics.update(p.raw_data.narrative_topics)
        
        # Expect ~3 topics per creator on average
        expected_unique = len(profiles) * 2
        topic_diversity = min(1.0, len(all_topics) / expected_unique)
        
        # Weighted average
        diversity = (
            platform_diversity * 0.35 +
            tier_diversity * 0.35 +
            topic_diversity * 0.30
        )
        
        return max(0.0, min(1.0, diversity))
    
    def _get_follower_tier(self, profile: InfluencerProfile) -> str:
        """Classify creator by follower count"""
        followers = profile.raw_data.metrics.followers
        
        if followers < 10000:
            return "nano"
        elif followers < 50000:
            return "micro"
        elif followers < 500000:
            return "mid"
        elif followers < 1000000:
            return "macro"
        else:
            return "mega"
    
    def simulate_campaign_outcomes(
        self,
        pack: InfluencerPack,
        virality_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Simulate expected campaign outcomes.
        
        Args:
            pack: Influencer pack
            virality_factor: Multiplier for viral spread (1.0 = no viral boost)
        
        Returns:
            Dict with simulated outcomes
        """
        # Base outcomes from pack
        base_impressions = pack.total_expected_impressions
        base_engagement = pack.total_expected_engagement
        
        # Apply virality factor
        total_impressions = int(base_impressions * virality_factor)
        total_engagement = int(base_engagement * virality_factor)
        
        # Estimate reach (unique viewers, ~70% of impressions)
        total_reach = int(total_impressions * 0.7)
        
        # Estimate conversions (streams, follows, etc.)
        # Assume 2% of engaged users convert
        estimated_conversions = int(total_engagement * 0.02)
        
        # ROI estimate
        # Assume $0.50 value per conversion (stream, follow, etc.)
        estimated_value_usd = estimated_conversions * 0.50
        roi = (estimated_value_usd / pack.total_budget_usd) if pack.total_budget_usd > 0 else 0
        
        return {
            'total_impressions': total_impressions,
            'total_reach': total_reach,
            'total_engagement': total_engagement,
            'estimated_conversions': estimated_conversions,
            'estimated_value_usd': round(estimated_value_usd, 2),
            'roi': round(roi, 2),
            'cost_per_impression': round(pack.total_budget_usd / total_impressions * 1000, 2) if total_impressions > 0 else 0,
            'cost_per_engagement': round(pack.total_budget_usd / total_engagement, 2) if total_engagement > 0 else 0,
            'cost_per_conversion': round(pack.total_budget_usd / estimated_conversions, 2) if estimated_conversions > 0 else 0
        }


if __name__ == "__main__":
    # Example usage
    from .influencer_scraper import InfluencerScraper
    from .influencer_analysis import InfluencerAnalyzer
    
    # Create sample profiles
    scraper = InfluencerScraper()
    analyzer = InfluencerAnalyzer()
    selector = InfluencerSelector()
    
    # Scrape and analyze multiple creators
    urls = [
        "https://www.tiktok.com/@creator1",
        "https://www.tiktok.com/@creator2",
        "https://www.instagram.com/@creator3",
        "https://www.instagram.com/@creator4",
        "https://www.youtube.com/@creator5",
        "https://www.tiktok.com/@creator6",
        "https://www.tiktok.com/@creator7",
        "https://www.instagram.com/@creator8"
    ]
    
    raw_data_list = scraper.scrape_multiple(urls)
    profiles = analyzer.analyze_batch(raw_data_list)
    
    # Select optimal pack
    pack = selector.select_optimal_pack(
        candidates=profiles,
        budget_usd=5000.0
    )
    
    if pack:
        print("✓ Optimal pack selected")
        print(f"\n  Pack ID: {pack.pack_id}")
        print(f"  Primary creators: {len(pack.primary_creators)}")
        print(f"  Support creators: {len(pack.support_creators)}")
        print(f"  Total budget: ${pack.total_budget_usd:,.2f}")
        print(f"  Expected impressions: {pack.total_expected_impressions:,}")
        print(f"  Average CPM: ${pack.average_cpm:.2f}")
        print(f"  Diversity: {pack.diversity_score:.2f}")
        print(f"  Max risk: {pack.max_risk_score:.2f}")
        print(f"  Recommended satellites: {pack.satellite_sync_count}")
        
        # Simulate outcomes
        outcomes = selector.simulate_campaign_outcomes(pack, virality_factor=1.5)
        print(f"\n  Simulated outcomes (1.5x virality):")
        print(f"    Total reach: {outcomes['total_reach']:,}")
        print(f"    Estimated conversions: {outcomes['estimated_conversions']:,}")
        print(f"    Estimated ROI: {outcomes['roi']:.2f}x")
    else:
        print("❌ Failed to create pack")
