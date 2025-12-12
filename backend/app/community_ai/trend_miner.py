"""
Trend Miner - Trend Analysis System for Community Manager AI

Extracts and analyzes trends from TikTok, Instagram, YouTube, and satellite channels.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from .models import (
    TrendItem,
    TrendAnalysis,
    TrendCategory,
    Platform
)

logger = logging.getLogger(__name__)


class TrendMiner:
    """
    Trend analysis and mining system.
    
    Analyzes trends from:
    - TikTok
    - Instagram
    - YouTube
    - Official channel
    - Satellite channels
    
    Classifies by rhythm, visuals, storytelling, engagement.
    """
    
    def __init__(self, mode: str = "live"):
        """
        Initialize trend miner.
        
        Args:
            mode: "live" or "stub"
        """
        self.mode = mode
    
    def extract_trending_patterns(
        self,
        platform: Platform,
        time_window_days: int = 7,
        min_engagement: float = 0.05
    ) -> List[TrendItem]:
        """
        Extract trending patterns from platform.
        
        Args:
            platform: Target platform
            time_window_days: Days to analyze
            min_engagement: Minimum engagement threshold
        
        Returns:
            List of trending items
        """
        logger.info(f"📈 Mining trends from {platform.value} (last {time_window_days} days)")
        
        if self.mode == "stub":
            return self._stub_trends(platform)
        
        # LIVE mode: real API calls
        # TODO: Implement real API integrations
        trends = []
        
        # Placeholder for API integration
        # trends = self._fetch_from_api(platform, time_window_days)
        
        return trends
    
    def analyze_global_trends(
        self,
        platforms: List[Platform] = None,
        brand_rules: Optional[Dict[str, Any]] = None
    ) -> TrendAnalysis:
        """
        Analyze trends across all platforms.
        
        Args:
            platforms: List of platforms to analyze (default: all)
            brand_rules: Brand rules for filtering
        
        Returns:
            Complete trend analysis
        """
        if platforms is None:
            platforms = [Platform.TIKTOK, Platform.INSTAGRAM, Platform.YOUTUBE]
        
        logger.info(f"🌍 Analyzing global trends across {len(platforms)} platforms")
        
        all_trends = []
        for platform in platforms:
            trends = self.extract_trending_patterns(platform)
            all_trends.extend(trends)
        
        # Classify trends
        trending_now = [t for t in all_trends if t.growth_rate > 1.5]
        rising_trends = [t for t in all_trends if 1.0 < t.growth_rate <= 1.5]
        declining_trends = [t for t in all_trends if t.growth_rate < 0.8]
        
        # Filter by brand fit
        if brand_rules:
            trending_now = [t for t in trending_now if t.brand_fit_score >= 0.7]
        
        # Generate recommendations
        apply_immediately = [t.name for t in trending_now[:3] if t.brand_fit_score >= 0.85]
        test_in_satellites = [t.name for t in rising_trends[:5]]
        avoid = [t.name for t in all_trends if t.brand_fit_score < 0.3]
        
        summary = self._generate_summary(trending_now, rising_trends, declining_trends)
        
        analysis = TrendAnalysis(
            analysis_id=f"trend_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            analyzed_at=datetime.utcnow(),
            trending_now=trending_now,
            rising_trends=rising_trends,
            declining_trends=declining_trends,
            apply_immediately=apply_immediately,
            test_in_satellites=test_in_satellites,
            avoid=avoid,
            summary=summary,
            confidence=0.82
        )
        
        logger.info(f"✅ Analysis complete: {len(trending_now)} hot trends, {len(rising_trends)} rising")
        return analysis
    
    def classify_trend(
        self,
        trend_data: Dict[str, Any],
        brand_rules: Optional[Dict[str, Any]] = None
    ) -> TrendItem:
        """
        Classify a single trend.
        
        Args:
            trend_data: Raw trend data
            brand_rules: Brand rules for scoring
        
        Returns:
            Classified TrendItem
        """
        # Extract classification
        rhythm = self._classify_rhythm(trend_data)
        visual_dominance = self._classify_visuals(trend_data)
        storytelling = self._classify_storytelling(trend_data)
        
        # Calculate brand fit
        brand_fit = self._calculate_brand_fit(trend_data, brand_rules)
        
        # Determine action
        recommended_action = self._recommend_action(trend_data, brand_fit)
        
        return TrendItem(
            trend_id=trend_data.get("id", "unknown"),
            category=TrendCategory(trend_data.get("category", "visual")),
            name=trend_data.get("name", "Unnamed Trend"),
            description=trend_data.get("description", ""),
            engagement_score=trend_data.get("engagement_score", 0.5),
            growth_rate=trend_data.get("growth_rate", 1.0),
            volume=trend_data.get("volume", 0),
            rhythm=rhythm,
            visual_dominance=visual_dominance,
            storytelling_style=storytelling,
            brand_fit_score=brand_fit,
            applicable_to_stakazo=brand_fit >= 0.7,
            recommended_action=recommended_action,
            detected_at=datetime.utcnow(),
            platform=Platform(trend_data.get("platform", "tiktok"))
        )
    
    def _classify_rhythm(self, trend_data: Dict[str, Any]) -> str:
        """Classify rhythm/pace of trend."""
        pace_indicators = {
            "fast": ["quick cuts", "aggressive", "high energy", "rapid"],
            "medium": ["steady", "moderate", "balanced"],
            "slow": ["cinematic", "slow motion", "atmospheric", "moody"]
        }
        
        description = trend_data.get("description", "").lower()
        
        for pace, keywords in pace_indicators.items():
            if any(kw in description for kw in keywords):
                return pace
        
        return "medium"
    
    def _classify_visuals(self, trend_data: Dict[str, Any]) -> str:
        """Classify visual dominance."""
        visual_types = {
            "color_grading": ["color", "grading", "filter", "lut"],
            "transitions": ["transition", "cut", "wipe", "morph"],
            "effects": ["effect", "vfx", "particles", "glow"],
            "composition": ["framing", "composition", "angle", "shot"]
        }
        
        description = trend_data.get("description", "").lower()
        
        for visual_type, keywords in visual_types.items():
            if any(kw in description for kw in keywords):
                return visual_type
        
        return "general"
    
    def _classify_storytelling(self, trend_data: Dict[str, Any]) -> str:
        """Classify storytelling style."""
        story_types = {
            "narrative": ["story", "narrative", "arc", "journey"],
            "vibe": ["vibe", "mood", "aesthetic", "atmosphere"],
            "comedic": ["funny", "comedy", "humor", "joke"],
            "motivational": ["motivation", "inspiration", "hustle", "grind"]
        }
        
        description = trend_data.get("description", "").lower()
        
        for story_type, keywords in story_types.items():
            if any(kw in description for kw in keywords):
                return story_type
        
        return "vibe"
    
    def _calculate_brand_fit(
        self,
        trend_data: Dict[str, Any],
        brand_rules: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate how well trend fits brand."""
        if not brand_rules:
            return 0.7  # Default neutral score
        
        score = 0.5  # Base score
        
        # Check aesthetic alignment
        if "aesthetic" in brand_rules:
            brand_colors = brand_rules["aesthetic"].get("colors", [])
            trend_colors = trend_data.get("colors", [])
            
            if any(color in trend_colors for color in brand_colors):
                score += 0.2
        
        # Check prohibitions
        if "prohibitions" in brand_rules:
            prohibitions = brand_rules["prohibitions"]
            description = trend_data.get("description", "").lower()
            
            if any(prohibition.lower() in description for prohibition in prohibitions):
                score -= 0.3
        
        # Check content themes
        if "content" in brand_rules:
            themes = brand_rules["content"].get("themes", [])
            trend_themes = trend_data.get("themes", [])
            
            if any(theme in trend_themes for theme in themes):
                score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _recommend_action(self, trend_data: Dict[str, Any], brand_fit: float) -> str:
        """Recommend action for trend."""
        if brand_fit >= 0.85:
            return "Apply immediately to official channel"
        elif brand_fit >= 0.70:
            return "Test in official channel with careful monitoring"
        elif brand_fit >= 0.50:
            return "Test in satellite channels for learning"
        else:
            return "Avoid - low brand fit"
    
    def _generate_summary(
        self,
        trending: List[TrendItem],
        rising: List[TrendItem],
        declining: List[TrendItem]
    ) -> str:
        """Generate analysis summary."""
        parts = []
        
        parts.append(f"{len(trending)} hot trends detected")
        
        if trending:
            top_category = max(set(t.category for t in trending), key=lambda c: sum(1 for t in trending if t.category == c))
            parts.append(f"Dominant category: {top_category.value}")
        
        applicable = [t for t in trending if t.applicable_to_stakazo]
        parts.append(f"{len(applicable)} applicable to Stakazo brand")
        
        return ". ".join(parts)
    
    def _stub_trends(self, platform: Platform) -> List[TrendItem]:
        """Generate stub trends for testing."""
        return [
            TrendItem(
                trend_id=f"stub_trend_1_{platform.value}",
                category=TrendCategory.VISUAL,
                name="Purple Neon Night Aesthetic",
                description="Purple and blue neon lights in night scenes with cars",
                engagement_score=0.85,
                growth_rate=1.8,
                volume=15000,
                rhythm="medium",
                visual_dominance="color_grading",
                storytelling_style="vibe",
                brand_fit_score=0.92,
                applicable_to_stakazo=True,
                recommended_action="Apply immediately to official channel",
                detected_at=datetime.utcnow(),
                platform=platform
            ),
            TrendItem(
                trend_id=f"stub_trend_2_{platform.value}",
                category=TrendCategory.FORMAT,
                name="Fast Cut Transitions",
                description="Aggressive cutting on beat with high energy",
                engagement_score=0.78,
                growth_rate=1.5,
                volume=25000,
                rhythm="fast",
                visual_dominance="transitions",
                storytelling_style="vibe",
                brand_fit_score=0.75,
                applicable_to_stakazo=True,
                recommended_action="Test in official channel with careful monitoring",
                detected_at=datetime.utcnow(),
                platform=platform
            ),
            TrendItem(
                trend_id=f"stub_trend_3_{platform.value}",
                category=TrendCategory.NARRATIVE,
                name="Rags to Riches Story",
                description="Visual storytelling of success journey",
                engagement_score=0.82,
                growth_rate=1.3,
                volume=12000,
                rhythm="medium",
                visual_dominance="composition",
                storytelling_style="narrative",
                brand_fit_score=0.88,
                applicable_to_stakazo=True,
                recommended_action="Apply immediately to official channel",
                detected_at=datetime.utcnow(),
                platform=platform
            )
        ]
