"""
Sprint 16: Influencer Trend Engine - Influencer Analysis

Analyzes influencer profiles and calculates comprehensive scores.

Scoring Metrics (0-1 scale):
1. impact_score - Reach and engagement quality
2. credibility_score - Consistency and audience quality
3. cultural_fit - Alignment with STAKAZO/Lendas Daría
4. trend_reactivity - Speed and trend adoption rate
5. risk_score - Saturation and controversy risk
6. price_efficiency - CPM vs market average

Author: STAKAZO Project
Date: 2025-12-12
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import statistics

from .influencer_scraper import (
    InfluencerRawData,
    Platform,
    PostingFrequency
)


@dataclass
class InfluencerScores:
    """Calculated scores for an influencer"""
    impact_score: float  # 0-1: reach + engagement quality
    credibility_score: float  # 0-1: consistency + audience quality
    cultural_fit: float  # 0-1: alignment with brand aesthetic
    trend_reactivity: float  # 0-1: speed + adoption rate
    risk_score: float  # 0-1: saturation + controversy (higher = riskier)
    price_efficiency: float  # 0-1: CPM vs market (higher = better deal)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'impact_score': self.impact_score,
            'credibility_score': self.credibility_score,
            'cultural_fit': self.cultural_fit,
            'trend_reactivity': self.trend_reactivity,
            'risk_score': self.risk_score,
            'price_efficiency': self.price_efficiency
        }
    
    def composite_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted composite score"""
        if weights is None:
            # Default weights
            weights = {
                'impact_score': 0.25,
                'credibility_score': 0.20,
                'cultural_fit': 0.25,
                'trend_reactivity': 0.15,
                'risk_score': -0.10,  # Negative weight (lower risk is better)
                'price_efficiency': 0.05
            }
        
        score = (
            self.impact_score * weights.get('impact_score', 0.25) +
            self.credibility_score * weights.get('credibility_score', 0.20) +
            self.cultural_fit * weights.get('cultural_fit', 0.25) +
            self.trend_reactivity * weights.get('trend_reactivity', 0.15) +
            self.risk_score * weights.get('risk_score', -0.10) +
            self.price_efficiency * weights.get('price_efficiency', 0.05)
        )
        
        return max(0.0, min(1.0, score))


@dataclass
class InfluencerProfile:
    """Complete analyzed profile for an influencer"""
    raw_data: InfluencerRawData
    scores: InfluencerScores
    strengths: List[str]
    weaknesses: List[str]
    recommended_use_case: str
    estimated_cpm_usd: float
    audience_quality: str  # "excellent", "good", "average", "poor"
    content_consistency: str  # "very_high", "high", "medium", "low"
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_data': self.raw_data.to_dict(),
            'scores': self.scores.to_dict(),
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommended_use_case': self.recommended_use_case,
            'estimated_cpm_usd': self.estimated_cpm_usd,
            'audience_quality': self.audience_quality,
            'content_consistency': self.content_consistency,
            'analyzed_at': self.analyzed_at.isoformat()
        }


class InfluencerAnalyzer:
    """
    Analyzes influencer profiles and generates scores.
    
    Methodology:
    - Impact: Follower count + engagement quality + view ratio
    - Credibility: Posting consistency + engagement pattern + verification
    - Cultural fit: Topics + style + language + cultural markers
    - Trend reactivity: Posting frequency + trend participation history
    - Risk: Over-saturation + controversy indicators + engagement drops
    - Price efficiency: Estimated CPM vs market benchmarks
    """
    
    def __init__(
        self,
        target_brand: str = "STAKAZO",
        target_aesthetic: List[str] = None,
        market_cpm_benchmarks: Optional[Dict[str, float]] = None
    ):
        """
        Initialize analyzer.
        
        Args:
            target_brand: Brand name for cultural fit analysis
            target_aesthetic: Target aesthetic keywords
            market_cpm_benchmarks: CPM benchmarks by platform (USD)
        """
        self.target_brand = target_brand.lower()
        
        if target_aesthetic is None:
            self.target_aesthetic = [
                "urban", "gen-z", "latam", "music", "lifestyle",
                "authentic", "creative", "bold", "diverse"
            ]
        else:
            self.target_aesthetic = [a.lower() for a in target_aesthetic]
        
        if market_cpm_benchmarks is None:
            self.market_cpm_benchmarks = {
                Platform.TIKTOK.value: 8.0,  # $8 CPM
                Platform.INSTAGRAM.value: 12.0,  # $12 CPM
                Platform.YOUTUBE.value: 15.0  # $15 CPM
            }
        else:
            self.market_cpm_benchmarks = market_cpm_benchmarks
    
    def analyze(self, raw_data: InfluencerRawData) -> InfluencerProfile:
        """
        Perform complete analysis on influencer.
        
        Args:
            raw_data: Scraped influencer data
        
        Returns:
            InfluencerProfile with scores and insights
        """
        # Calculate all scores
        impact = self._calculate_impact_score(raw_data)
        credibility = self._calculate_credibility_score(raw_data)
        cultural_fit = self._calculate_cultural_fit(raw_data)
        trend_reactivity = self._calculate_trend_reactivity(raw_data)
        risk = self._calculate_risk_score(raw_data)
        price_efficiency = self._calculate_price_efficiency(raw_data)
        
        scores = InfluencerScores(
            impact_score=impact,
            credibility_score=credibility,
            cultural_fit=cultural_fit,
            trend_reactivity=trend_reactivity,
            risk_score=risk,
            price_efficiency=price_efficiency
        )
        
        # Generate insights
        strengths = self._identify_strengths(raw_data, scores)
        weaknesses = self._identify_weaknesses(raw_data, scores)
        use_case = self._recommend_use_case(raw_data, scores)
        
        # Estimate CPM
        estimated_cpm = self._estimate_cpm(raw_data)
        
        # Audience quality
        audience_quality = self._assess_audience_quality(raw_data)
        
        # Content consistency
        content_consistency = self._assess_content_consistency(raw_data)
        
        return InfluencerProfile(
            raw_data=raw_data,
            scores=scores,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_use_case=use_case,
            estimated_cpm_usd=estimated_cpm,
            audience_quality=audience_quality,
            content_consistency=content_consistency
        )
    
    def analyze_batch(
        self,
        raw_data_list: List[InfluencerRawData]
    ) -> List[InfluencerProfile]:
        """Analyze multiple influencers"""
        return [self.analyze(raw_data) for raw_data in raw_data_list]
    
    def _calculate_impact_score(self, data: InfluencerRawData) -> float:
        """
        Calculate impact score (0-1).
        
        Factors:
        - Follower count (scaled by platform)
        - Engagement rate
        - View-to-follower ratio
        """
        # Follower score (logarithmic scaling)
        follower_score = min(1.0, data.metrics.followers / 500000)  # 500k = max
        
        # Engagement score (high engagement = higher score)
        # Good engagement: >5% for TikTok, >3% for Instagram, >2% for YouTube
        platform_thresholds = {
            Platform.TIKTOK: 0.05,
            Platform.INSTAGRAM: 0.03,
            Platform.YOUTUBE: 0.02
        }
        threshold = platform_thresholds.get(data.platform, 0.03)
        engagement_score = min(1.0, data.metrics.engagement_rate / threshold)
        
        # View ratio score
        view_ratio_score = min(1.0, data.metrics.view_to_follower_ratio / 2.0)
        
        # Weighted average
        impact = (
            follower_score * 0.4 +
            engagement_score * 0.35 +
            view_ratio_score * 0.25
        )
        
        return max(0.0, min(1.0, impact))
    
    def _calculate_credibility_score(self, data: InfluencerRawData) -> float:
        """
        Calculate credibility score (0-1).
        
        Factors:
        - Posting consistency
        - Engagement pattern (not bot-driven)
        - Verification status
        - Content volume
        """
        # Consistency score (medium-high frequency is best)
        frequency_scores = {
            PostingFrequency.VERY_HIGH: 0.7,  # Too much can signal desperation
            PostingFrequency.HIGH: 1.0,
            PostingFrequency.MEDIUM: 0.9,
            PostingFrequency.LOW: 0.6,
            PostingFrequency.VERY_LOW: 0.3
        }
        consistency_score = frequency_scores[data.metrics.posting_frequency]
        
        # Engagement pattern (comments-to-likes ratio)
        # Healthy ratio: 2-5% comments per like
        comment_ratio = data.metrics.avg_comments / max(1, data.metrics.avg_likes)
        pattern_score = 1.0 if 0.02 <= comment_ratio <= 0.05 else 0.7
        
        # Verification bonus
        verification_score = 1.0 if data.verified else 0.8
        
        # Content volume (more posts = more track record)
        volume_score = min(1.0, data.metrics.total_posts / 200)
        
        # Weighted average
        credibility = (
            consistency_score * 0.35 +
            pattern_score * 0.25 +
            verification_score * 0.20 +
            volume_score * 0.20
        )
        
        return max(0.0, min(1.0, credibility))
    
    def _calculate_cultural_fit(self, data: InfluencerRawData) -> float:
        """
        Calculate cultural fit score (0-1).
        
        Factors:
        - Narrative topics alignment
        - Video style alignment
        - Cultural markers
        - Language
        """
        # Topics alignment
        topic_matches = sum(
            1 for topic in data.narrative_topics
            if any(aesthetic in topic.lower() for aesthetic in self.target_aesthetic)
        )
        topic_score = topic_matches / max(1, len(data.narrative_topics))
        
        # Style alignment
        style_keywords = ["authentic", "raw", "urban", "creative", "bold"]
        style_matches = sum(
            1 for style in data.video_styles
            if any(keyword in style.lower() for keyword in style_keywords)
        )
        style_score = style_matches / max(1, len(data.video_styles))
        
        # Cultural markers alignment
        marker_matches = sum(
            1 for marker in data.cultural_markers
            if marker.lower() in self.target_aesthetic
        )
        marker_score = marker_matches / max(1, len(data.cultural_markers))
        
        # Language (Spanish = perfect fit for STAKAZO)
        language_score = 1.0 if data.language == "es" else 0.7
        
        # Weighted average
        cultural_fit = (
            topic_score * 0.35 +
            style_score * 0.25 +
            marker_score * 0.25 +
            language_score * 0.15
        )
        
        return max(0.0, min(1.0, cultural_fit))
    
    def _calculate_trend_reactivity(self, data: InfluencerRawData) -> float:
        """
        Calculate trend reactivity score (0-1).
        
        Factors:
        - Posting frequency (more = faster to react)
        - Trend-related video styles
        - Recency of last post
        """
        # Frequency score
        frequency_scores = {
            PostingFrequency.VERY_HIGH: 1.0,
            PostingFrequency.HIGH: 0.9,
            PostingFrequency.MEDIUM: 0.7,
            PostingFrequency.LOW: 0.4,
            PostingFrequency.VERY_LOW: 0.2
        }
        frequency_score = frequency_scores[data.metrics.posting_frequency]
        
        # Trend style indicators
        trend_keywords = ["trends", "challenge", "viral", "fast-cut", "meme"]
        trend_matches = sum(
            1 for style in data.video_styles
            if any(keyword in style.lower() for keyword in trend_keywords)
        )
        trend_style_score = min(1.0, trend_matches / 2.0)
        
        # Recency score (last post within 7 days = active)
        if data.last_post_date:
            days_since_post = (datetime.now() - data.last_post_date).days
            recency_score = max(0.0, 1.0 - (days_since_post / 14))
        else:
            recency_score = 0.5
        
        # Weighted average
        reactivity = (
            frequency_score * 0.45 +
            trend_style_score * 0.30 +
            recency_score * 0.25
        )
        
        return max(0.0, min(1.0, reactivity))
    
    def _calculate_risk_score(self, data: InfluencerRawData) -> float:
        """
        Calculate risk score (0-1, higher = riskier).
        
        Factors:
        - Over-saturation (too many posts)
        - Low engagement despite high followers (bought followers?)
        - Controversy indicators in bio/topics
        """
        # Saturation risk (posting too much)
        saturation_risk = 0.0
        if data.metrics.posting_frequency == PostingFrequency.VERY_HIGH:
            saturation_risk = 0.4
        
        # Fake followers risk (low engagement despite high followers)
        engagement_ratio = data.metrics.engagement_rate
        if data.metrics.followers > 50000 and engagement_ratio < 0.01:
            fake_followers_risk = 0.6
        elif data.metrics.followers > 100000 and engagement_ratio < 0.02:
            fake_followers_risk = 0.4
        else:
            fake_followers_risk = 0.0
        
        # Controversy risk (simple keyword check)
        controversy_keywords = ["drama", "polemic", "scandal", "controversy"]
        controversy_risk = 0.3 if any(
            keyword in data.bio.lower() or
            any(keyword in topic.lower() for topic in data.narrative_topics)
            for keyword in controversy_keywords
        ) else 0.0
        
        # View-to-follower mismatch (views << followers)
        if data.metrics.view_to_follower_ratio < 0.1:
            mismatch_risk = 0.5
        else:
            mismatch_risk = 0.0
        
        # Combine risks (max, not sum, to avoid over-penalizing)
        total_risk = max(
            saturation_risk,
            fake_followers_risk,
            controversy_risk,
            mismatch_risk
        )
        
        return max(0.0, min(1.0, total_risk))
    
    def _calculate_price_efficiency(self, data: InfluencerRawData) -> float:
        """
        Calculate price efficiency score (0-1, higher = better deal).
        
        Compare estimated CPM to market average.
        """
        estimated_cpm = self._estimate_cpm(data)
        market_avg = self.market_cpm_benchmarks.get(data.platform.value, 10.0)
        
        # Lower CPM = better efficiency
        # If estimated CPM is 50% of market, efficiency = 1.0
        # If estimated CPM = market, efficiency = 0.5
        # If estimated CPM is 2x market, efficiency = 0.0
        efficiency = max(0.0, 1.0 - (estimated_cpm / (market_avg * 2)))
        
        return max(0.0, min(1.0, efficiency))
    
    def _estimate_cpm(self, data: InfluencerRawData) -> float:
        """
        Estimate CPM (cost per thousand impressions) in USD.
        
        Based on:
        - Platform baseline
        - Follower count
        - Engagement quality
        """
        # Platform baseline
        baseline = self.market_cpm_benchmarks.get(data.platform.value, 10.0)
        
        # Adjust for follower count (micro = cheaper, macro = more expensive)
        if data.metrics.followers < 10000:
            follower_multiplier = 0.5
        elif data.metrics.followers < 50000:
            follower_multiplier = 0.7
        elif data.metrics.followers < 100000:
            follower_multiplier = 1.0
        elif data.metrics.followers < 500000:
            follower_multiplier = 1.3
        else:
            follower_multiplier = 1.5
        
        # Adjust for engagement (high engagement = premium)
        if data.metrics.engagement_rate > 0.05:
            engagement_multiplier = 1.3
        elif data.metrics.engagement_rate > 0.03:
            engagement_multiplier = 1.1
        else:
            engagement_multiplier = 0.9
        
        estimated_cpm = baseline * follower_multiplier * engagement_multiplier
        
        return round(estimated_cpm, 2)
    
    def _identify_strengths(
        self,
        data: InfluencerRawData,
        scores: InfluencerScores
    ) -> List[str]:
        """Identify top strengths"""
        strengths = []
        
        if scores.impact_score > 0.7:
            strengths.append("High reach and engagement")
        
        if scores.credibility_score > 0.7:
            strengths.append("Consistent and credible content")
        
        if scores.cultural_fit > 0.7:
            strengths.append("Perfect cultural alignment")
        
        if scores.trend_reactivity > 0.7:
            strengths.append("Fast trend adoption")
        
        if scores.risk_score < 0.3:
            strengths.append("Low risk profile")
        
        if scores.price_efficiency > 0.6:
            strengths.append("Cost-effective")
        
        if data.verified:
            strengths.append("Verified account")
        
        if data.metrics.engagement_rate > 0.05:
            strengths.append("Exceptional engagement rate")
        
        return strengths[:5]  # Top 5
    
    def _identify_weaknesses(
        self,
        data: InfluencerRawData,
        scores: InfluencerScores
    ) -> List[str]:
        """Identify main weaknesses"""
        weaknesses = []
        
        if scores.impact_score < 0.4:
            weaknesses.append("Limited reach or engagement")
        
        if scores.credibility_score < 0.5:
            weaknesses.append("Inconsistent posting or suspicious patterns")
        
        if scores.cultural_fit < 0.5:
            weaknesses.append("Weak cultural alignment")
        
        if scores.trend_reactivity < 0.5:
            weaknesses.append("Slow to adopt trends")
        
        if scores.risk_score > 0.5:
            weaknesses.append("High risk indicators")
        
        if scores.price_efficiency < 0.3:
            weaknesses.append("Expensive relative to market")
        
        if data.metrics.engagement_rate < 0.02:
            weaknesses.append("Low engagement rate")
        
        return weaknesses[:5]  # Top 5
    
    def _recommend_use_case(
        self,
        data: InfluencerRawData,
        scores: InfluencerScores
    ) -> str:
        """Recommend optimal use case"""
        # Primary driver: high impact + cultural fit + low risk
        if (scores.impact_score > 0.7 and 
            scores.cultural_fit > 0.7 and 
            scores.risk_score < 0.3):
            return "primary_driver"
        
        # Support amplifier: good reach, fast reactivity
        elif (scores.impact_score > 0.5 and 
              scores.trend_reactivity > 0.6):
            return "support_amplifier"
        
        # Budget option: cost-effective with decent fit
        elif (scores.price_efficiency > 0.7 and 
              scores.cultural_fit > 0.5):
            return "budget_option"
        
        # Niche specialist: perfect cultural fit but smaller reach
        elif (scores.cultural_fit > 0.8 and 
              scores.credibility_score > 0.6):
            return "niche_specialist"
        
        # Avoid: high risk or poor fit
        elif scores.risk_score > 0.6 or scores.cultural_fit < 0.3:
            return "avoid"
        
        else:
            return "secondary_option"
    
    def _assess_audience_quality(self, data: InfluencerRawData) -> str:
        """Assess audience quality"""
        engagement = data.metrics.engagement_rate
        view_ratio = data.metrics.view_to_follower_ratio
        
        if engagement > 0.05 and view_ratio > 0.5:
            return "excellent"
        elif engagement > 0.03 and view_ratio > 0.3:
            return "good"
        elif engagement > 0.015:
            return "average"
        else:
            return "poor"
    
    def _assess_content_consistency(self, data: InfluencerRawData) -> str:
        """Assess content consistency"""
        freq = data.metrics.posting_frequency
        
        if freq in [PostingFrequency.HIGH, PostingFrequency.VERY_HIGH]:
            return "very_high"
        elif freq == PostingFrequency.MEDIUM:
            return "high"
        elif freq == PostingFrequency.LOW:
            return "medium"
        else:
            return "low"


if __name__ == "__main__":
    # Example usage
    from .influencer_scraper import InfluencerScraper
    
    scraper = InfluencerScraper()
    analyzer = InfluencerAnalyzer()
    
    # Scrape and analyze
    url = "https://www.tiktok.com/@example_creator"
    raw_data = scraper.scrape_influencer(url)
    
    if raw_data:
        profile = analyzer.analyze(raw_data)
        
        print("✓ Analysis complete")
        print(f"  Impact: {profile.scores.impact_score:.2f}")
        print(f"  Credibility: {profile.scores.credibility_score:.2f}")
        print(f"  Cultural fit: {profile.scores.cultural_fit:.2f}")
        print(f"  Trend reactivity: {profile.scores.trend_reactivity:.2f}")
        print(f"  Risk: {profile.scores.risk_score:.2f}")
        print(f"  Price efficiency: {profile.scores.price_efficiency:.2f}")
        print(f"  Composite score: {profile.scores.composite_score():.2f}")
        print(f"  Recommended: {profile.recommended_use_case}")
        print(f"  Strengths: {', '.join(profile.strengths)}")
