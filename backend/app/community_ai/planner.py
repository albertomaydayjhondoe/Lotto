"""
Planner - Daily Planning System for Community Manager AI

Generates intelligent daily content plans for official and satellite channels.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from .models import (
    DailyPlan,
    PostPlan,
    Platform,
    ContentType,
    ChannelType
)

logger = logging.getLogger(__name__)


class DailyPlanner:
    """
    Daily content planner for Community Manager AI.
    
    Integrates:
    - Brand Engine (BRAND_STATIC_RULES.json)
    - Vision Engine (visual metadata)
    - Satellite Engine (performance metrics)
    - ML historical patterns
    """
    
    def __init__(
        self,
        brand_rules_path: Optional[str] = None,
        mode: str = "live"
    ):
        """
        Initialize planner.
        
        Args:
            brand_rules_path: Path to BRAND_STATIC_RULES.json
            mode: "live" or "stub" (testing)
        """
        self.mode = mode
        self.brand_rules_path = brand_rules_path
        self.brand_rules: Optional[Dict[str, Any]] = None
        
        if brand_rules_path and mode == "live":
            self._load_brand_rules()
    
    def _load_brand_rules(self) -> None:
        """Load brand rules from JSON."""
        try:
            with open(self.brand_rules_path, 'r', encoding='utf-8') as f:
                self.brand_rules = json.load(f)
            logger.info(f"✅ Loaded brand rules from {self.brand_rules_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load brand rules: {e}")
            self.brand_rules = None
    
    def generate_daily_plan(
        self,
        user_id: str,
        date: datetime,
        metrics: Optional[Dict[str, Any]] = None,
        vision_metadata: Optional[List[Dict[str, Any]]] = None,
        satellite_data: Optional[Dict[str, Any]] = None
    ) -> DailyPlan:
        """
        Generate daily content plan.
        
        Args:
            user_id: Artist user ID
            date: Target date for plan
            metrics: Historical performance metrics
            vision_metadata: Visual metadata from Vision Engine
            satellite_data: Performance data from satellites
        
        Returns:
            DailyPlan with official and satellite posts
        """
        logger.info(f"📅 Generating daily plan for {date.date()}")
        
        # Generate official posts (brand-aligned)
        official_posts = self._generate_official_posts(
            user_id=user_id,
            date=date,
            metrics=metrics,
            vision_metadata=vision_metadata
        )
        
        # Generate satellite experiments (ML testing)
        satellite_experiments = self._generate_satellite_experiments(
            user_id=user_id,
            date=date,
            satellite_data=satellite_data
        )
        
        # Identify priority content
        priority_content = self._identify_priority_content(official_posts)
        
        # Calculate strategy
        strategy_summary = self._generate_strategy_summary(
            official_posts,
            satellite_experiments
        )
        
        # Estimate cost
        estimated_cost = self._estimate_cost(official_posts, satellite_experiments)
        
        plan = DailyPlan(
            plan_id=f"plan_{user_id}_{date.strftime('%Y%m%d')}",
            date=date,
            user_id=user_id,
            official_posts=official_posts,
            satellite_experiments=satellite_experiments,
            priority_content=priority_content,
            total_posts=len(official_posts) + len(satellite_experiments),
            official_count=len(official_posts),
            satellite_count=len(satellite_experiments),
            strategy_summary=strategy_summary,
            rationale=self._generate_rationale(metrics, satellite_data),
            confidence=0.85,
            estimated_cost_eur=estimated_cost,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"✅ Generated plan: {plan.official_count} official, {plan.satellite_count} satellite")
        return plan
    
    def _generate_official_posts(
        self,
        user_id: str,
        date: datetime,
        metrics: Optional[Dict[str, Any]],
        vision_metadata: Optional[List[Dict[str, Any]]]
    ) -> List[PostPlan]:
        """Generate official channel posts (brand-aligned)."""
        posts = []
        
        if self.mode == "stub":
            # Stub mode: return sample posts
            posts.append(PostPlan(
                post_id=f"official_{user_id}_{date.strftime('%Y%m%d')}_1",
                platform=Platform.INSTAGRAM,
                content_type=ContentType.REEL,
                channel_type=ChannelType.OFFICIAL,
                scheduled_time=date.replace(hour=20, minute=0),
                caption="🟣 Nuevo track en camino... #Trap #Stakazo",
                hashtags=["#Trap", "#Stakazo", "#NewMusic"],
                visual_concept="Purple neon aesthetic, night scene, sports car",
                aesthetic_tags=["purple", "neon", "night", "car"],
                brand_compliant=True,
                brand_score=0.92,
                expected_retention=0.78,
                expected_ctr=0.085,
                virality_score=0.82,
                rationale="High-performing aesthetic (purple neon) + optimal posting time (20:00)",
                confidence=0.88
            ))
            return posts
        
        # LIVE mode: real logic
        
        # Analyze best-performing aesthetics
        if metrics and "top_aesthetics" in metrics:
            top_aesthetic = metrics["top_aesthetics"][0]
            
            # Create post based on top aesthetic
            post = self._create_post_from_aesthetic(
                user_id=user_id,
                date=date,
                aesthetic=top_aesthetic,
                platform=Platform.INSTAGRAM,
                content_type=ContentType.REEL
            )
            
            # Validate against brand rules
            if self._validate_brand_compliance(post):
                posts.append(post)
        
        # Add story post
        story_post = self._create_story_post(user_id, date)
        if self._validate_brand_compliance(story_post):
            posts.append(story_post)
        
        return posts
    
    def _generate_satellite_experiments(
        self,
        user_id: str,
        date: datetime,
        satellite_data: Optional[Dict[str, Any]]
    ) -> List[PostPlan]:
        """Generate satellite experiment posts (ML testing)."""
        experiments = []
        
        if self.mode == "stub":
            # Stub mode: return sample experiments
            experiments.append(PostPlan(
                post_id=f"satellite_{user_id}_{date.strftime('%Y%m%d')}_1",
                platform=Platform.TIKTOK,
                content_type=ContentType.VIDEO,
                channel_type=ChannelType.SATELLITE,
                scheduled_time=date.replace(hour=14, minute=0),
                caption="Vibe check 🎵",
                hashtags=["#Viral", "#Music", "#Trap"],
                visual_concept="Aggressive cuts, trending effects, high energy",
                aesthetic_tags=["trending", "aggressive", "fast_cuts"],
                brand_compliant=False,  # Satellites don't need brand compliance
                brand_score=0.45,
                expected_retention=0.65,
                expected_ctr=0.12,
                virality_score=0.88,
                rationale="Test viral editing style for ML learning",
                confidence=0.72
            ))
            return experiments
        
        # LIVE mode: real experiments
        
        # Test trending formats
        if satellite_data and "trending_formats" in satellite_data:
            for trend in satellite_data["trending_formats"][:2]:
                exp = self._create_experiment_from_trend(
                    user_id=user_id,
                    date=date,
                    trend=trend
                )
                experiments.append(exp)
        
        return experiments
    
    def _create_post_from_aesthetic(
        self,
        user_id: str,
        date: datetime,
        aesthetic: Dict[str, Any],
        platform: Platform,
        content_type: ContentType
    ) -> PostPlan:
        """Create post based on aesthetic data."""
        return PostPlan(
            post_id=f"official_{user_id}_{date.strftime('%Y%m%d')}_{aesthetic['name']}",
            platform=platform,
            content_type=content_type,
            channel_type=ChannelType.OFFICIAL,
            scheduled_time=self._calculate_best_time(date),
            caption=self._generate_caption(aesthetic),
            hashtags=self._generate_hashtags(aesthetic),
            visual_concept=aesthetic.get("description", ""),
            aesthetic_tags=aesthetic.get("tags", []),
            brand_compliant=True,
            brand_score=aesthetic.get("brand_score", 0.8),
            expected_retention=aesthetic.get("avg_retention", 0.75),
            expected_ctr=0.08,
            virality_score=0.80,
            rationale=f"Top performing aesthetic: {aesthetic['name']}",
            confidence=0.85
        )
    
    def _create_story_post(self, user_id: str, date: datetime) -> PostPlan:
        """Create story post."""
        return PostPlan(
            post_id=f"story_{user_id}_{date.strftime('%Y%m%d')}",
            platform=Platform.INSTAGRAM,
            content_type=ContentType.STORY,
            channel_type=ChannelType.OFFICIAL,
            scheduled_time=date.replace(hour=12, minute=0),
            caption="",
            hashtags=[],
            visual_concept="Behind the scenes, studio vibes",
            aesthetic_tags=["bts", "studio", "authentic"],
            brand_compliant=True,
            brand_score=0.88,
            expected_retention=0.70,
            expected_ctr=0.05,
            virality_score=0.60,
            rationale="Daily connection with audience",
            confidence=0.90
        )
    
    def _create_experiment_from_trend(
        self,
        user_id: str,
        date: datetime,
        trend: Dict[str, Any]
    ) -> PostPlan:
        """Create experiment from trend."""
        return PostPlan(
            post_id=f"satellite_{user_id}_{date.strftime('%Y%m%d')}_{trend['name']}",
            platform=Platform.TIKTOK,
            content_type=ContentType.VIDEO,
            channel_type=ChannelType.SATELLITE,
            scheduled_time=self._calculate_experiment_time(date),
            caption=trend.get("caption", "🎵"),
            hashtags=trend.get("hashtags", []),
            visual_concept=trend.get("concept", "Trending format"),
            aesthetic_tags=trend.get("tags", []),
            brand_compliant=False,
            brand_score=0.50,
            expected_retention=0.65,
            expected_ctr=0.10,
            virality_score=trend.get("virality_score", 0.85),
            rationale=f"Test trend: {trend['name']}",
            confidence=0.75
        )
    
    def _validate_brand_compliance(self, post: PostPlan) -> bool:
        """Validate post against brand rules."""
        if not self.brand_rules or post.channel_type == ChannelType.SATELLITE:
            return True  # Satellites don't need compliance
        
        # Check prohibitions
        prohibitions = self.brand_rules.get("prohibitions", [])
        for prohibition in prohibitions:
            if prohibition.lower() in post.caption.lower():
                logger.warning(f"⚠️ Post violates prohibition: {prohibition}")
                return False
        
        # Check aesthetic compliance
        required_aesthetics = self.brand_rules.get("aesthetic", {}).get("mandatory", [])
        if required_aesthetics:
            # Check if post has at least one required aesthetic
            has_required = any(
                req.lower() in " ".join(post.aesthetic_tags).lower()
                for req in required_aesthetics
            )
            if not has_required:
                logger.warning(f"⚠️ Post missing required aesthetics")
                return False
        
        return True
    
    def _identify_priority_content(self, posts: List[PostPlan]) -> List[str]:
        """Identify must-post content."""
        priority = []
        for post in posts:
            if post.expected_retention > 0.75 or post.virality_score > 0.80:
                priority.append(post.post_id)
        return priority
    
    def _generate_strategy_summary(
        self,
        official: List[PostPlan],
        satellites: List[PostPlan]
    ) -> str:
        """Generate strategy summary."""
        return (
            f"Official: {len(official)} brand-aligned posts for audience connection. "
            f"Satellites: {len(satellites)} experiments for ML learning and trend testing."
        )
    
    def _generate_rationale(
        self,
        metrics: Optional[Dict[str, Any]],
        satellite_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate plan rationale."""
        parts = []
        
        if metrics:
            parts.append(f"Based on {metrics.get('total_content', 0)} historical data points")
        
        if satellite_data:
            parts.append(f"Incorporating {len(satellite_data.get('trending_formats', []))} trending formats")
        
        parts.append("Maintaining brand consistency while testing new approaches")
        
        return ". ".join(parts)
    
    def _calculate_best_time(self, date: datetime) -> datetime:
        """Calculate optimal posting time."""
        # TODO: Use historical data to determine best time
        # For now, default to 20:00 (8 PM)
        return date.replace(hour=20, minute=0, second=0, microsecond=0)
    
    def _calculate_experiment_time(self, date: datetime) -> datetime:
        """Calculate experiment posting time."""
        # Experiments at different times to test timing
        return date.replace(hour=14, minute=0, second=0, microsecond=0)
    
    def _generate_caption(self, aesthetic: Dict[str, Any]) -> str:
        """Generate caption from aesthetic."""
        # TODO: Use LLM to generate creative captions
        return f"🟣 {aesthetic.get('name', 'New content')} #Stakazo"
    
    def _generate_hashtags(self, aesthetic: Dict[str, Any]) -> List[str]:
        """Generate hashtags from aesthetic."""
        base_tags = ["#Stakazo", "#Trap"]
        aesthetic_tags = [f"#{tag}" for tag in aesthetic.get("tags", [])[:3]]
        return base_tags + aesthetic_tags
    
    def _estimate_cost(
        self,
        official: List[PostPlan],
        satellites: List[PostPlan]
    ) -> float:
        """Estimate execution cost."""
        # Base cost per post: €0.005
        # LLM caption generation: €0.002 per post
        total_posts = len(official) + len(satellites)
        return total_posts * 0.007
    
    def predict_best_post_time(
        self,
        platform: Platform,
        content_type: ContentType,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> datetime:
        """
        Predict best posting time based on historical data.
        
        Args:
            platform: Target platform
            content_type: Type of content
            historical_data: Historical performance by time
        
        Returns:
            Optimal datetime for posting
        """
        # Default times by platform
        default_times = {
            Platform.INSTAGRAM: 20,  # 8 PM
            Platform.TIKTOK: 19,     # 7 PM
            Platform.YOUTUBE: 18,    # 6 PM
        }
        
        hour = default_times.get(platform, 20)
        
        if historical_data and "best_hours" in historical_data:
            best_hours = historical_data["best_hours"].get(platform.value, [])
            if best_hours:
                hour = best_hours[0]
        
        now = datetime.utcnow()
        return now.replace(hour=hour, minute=0, second=0, microsecond=0)
