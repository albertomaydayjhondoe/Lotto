"""
Pydantic Models for Community Manager AI - Sprint 4B

All data structures for planning, recommendations, trends, sentiment, and reporting.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ========================================
# Enums
# ========================================

class ContentType(str, Enum):
    """Types of content."""
    REEL = "reel"
    STORY = "story"
    POST = "post"
    VIDEO = "video"
    CAROUSEL = "carousel"
    SHORT = "short"  # YouTube Shorts


class Platform(str, Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    SPOTIFY = "spotify"


class ChannelType(str, Enum):
    """Channel classification."""
    OFFICIAL = "official"  # Brand-aligned, curated content
    SATELLITE = "satellite"  # Experimental, ML testing


class SentimentType(str, Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class TrendCategory(str, Enum):
    """Trend categories."""
    VISUAL = "visual"
    AUDIO = "audio"
    NARRATIVE = "narrative"
    FORMAT = "format"
    HASHTAG = "hashtag"
    CHALLENGE = "challenge"


# ========================================
# Content Planning Models
# ========================================

class PostPlan(BaseModel):
    """Individual post plan."""
    post_id: str
    platform: Platform
    content_type: ContentType
    channel_type: ChannelType
    scheduled_time: datetime
    
    # Content details
    caption: str
    hashtags: List[str] = []
    visual_concept: str
    aesthetic_tags: List[str] = []
    
    # Brand validation
    brand_compliant: bool
    brand_score: float = Field(ge=0.0, le=1.0)
    
    # Performance expectations
    expected_retention: float = Field(ge=0.0, le=1.0)
    expected_ctr: float = Field(ge=0.0, le=1.0)
    virality_score: float = Field(ge=0.0, le=1.0)
    
    # Rationale
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # References
    video_asset_id: Optional[str] = None
    clip_id: Optional[str] = None


class DailyPlan(BaseModel):
    """Daily content plan."""
    plan_id: str
    date: datetime
    user_id: str
    
    # Official channel posts
    official_posts: List[PostPlan] = []
    
    # Satellite experiments
    satellite_experiments: List[PostPlan] = []
    
    # Priority content (must post today)
    priority_content: List[str] = []
    
    # Summary
    total_posts: int
    official_count: int
    satellite_count: int
    
    # Strategy
    strategy_summary: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Cost estimation
    estimated_cost_eur: float
    
    # Metadata
    created_at: datetime
    created_by: str = "community_ai"


# ========================================
# Content Recommendations
# ========================================

class CreativeRecommendation(BaseModel):
    """Creative content recommendation."""
    recommendation_id: str
    category: str  # "videoclip", "vestuario", "narrativa", "aesthetic", "concept"
    
    title: str
    description: str
    details: Dict[str, Any]
    
    # Visual elements
    color_palette: List[str] = []
    scene_types: List[str] = []
    objects: List[str] = []
    
    # Inspiration
    references: List[str] = []
    
    # Brand alignment
    brand_aligned: bool
    brand_score: float = Field(ge=0.0, le=1.0)
    
    # Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Metadata
    created_at: datetime


class VideoclipRecommendation(BaseModel):
    """Videoclip concept recommendation."""
    concept_id: str
    title: str
    narrative: str
    
    # Visual style
    aesthetic: str
    color_palette: List[str]
    scene_sequence: List[str]
    
    # Elements
    wardrobe: str
    props: List[str]
    lighting: str
    locations: List[str]
    
    # Mood
    emotional_tone: str
    target_emotion: str
    
    # Brand alignment
    brand_score: float = Field(ge=0.0, le=1.0)
    
    # Inspiration
    references: List[str] = []
    
    # Metadata
    created_at: datetime


# ========================================
# Trend Analysis
# ========================================

class TrendItem(BaseModel):
    """Individual trend."""
    trend_id: str
    category: TrendCategory
    
    # Description
    name: str
    description: str
    
    # Metrics
    engagement_score: float = Field(ge=0.0, le=1.0)
    growth_rate: float
    volume: int  # Number of posts
    
    # Classification
    rhythm: Optional[str] = None
    visual_dominance: Optional[str] = None
    storytelling_style: Optional[str] = None
    
    # Brand fit
    brand_fit_score: float = Field(ge=0.0, le=1.0)
    applicable_to_stakazo: bool
    
    # Actionable insights
    recommended_action: str
    
    # Metadata
    detected_at: datetime
    platform: Platform


class TrendAnalysis(BaseModel):
    """Trend analysis report."""
    analysis_id: str
    analyzed_at: datetime
    
    # Trends
    trending_now: List[TrendItem] = []
    rising_trends: List[TrendItem] = []
    declining_trends: List[TrendItem] = []
    
    # Recommendations
    apply_immediately: List[str] = []
    test_in_satellites: List[str] = []
    avoid: List[str] = []
    
    # Summary
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)


# ========================================
# Sentiment Analysis
# ========================================

class CommentAnalysis(BaseModel):
    """Individual comment sentiment."""
    comment_id: str
    text: str
    
    # Sentiment
    sentiment: SentimentType
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1 negative, 0 neutral, +1 positive
    
    # Topics
    topics: List[str] = []
    
    # Signals
    hype_signal: bool = False
    actionable_feedback: bool = False
    
    # Metadata
    platform: Platform
    post_id: str
    analyzed_at: datetime


class SentimentReport(BaseModel):
    """Sentiment analysis report."""
    report_id: str
    analyzed_at: datetime
    
    # Overview
    total_comments: int
    positive_count: int
    neutral_count: int
    negative_count: int
    
    positive_percentage: float
    negative_percentage: float
    
    # Average sentiment
    avg_sentiment_score: float = Field(ge=-1.0, le=1.0)
    
    # Topics
    top_topics: List[Dict[str, Any]] = []
    
    # Signals
    hype_detected: bool = False
    hype_topics: List[str] = []
    
    # Actionable insights
    insights: List[str] = []
    recommendations: List[str] = []
    
    # Metadata
    time_period_days: int
    confidence: float = Field(ge=0.0, le=1.0)


# ========================================
# Daily Reports
# ========================================

class PerformanceMetric(BaseModel):
    """Performance metric."""
    metric_name: str
    value: float
    change_percentage: float  # vs previous period
    trend: str  # "up", "down", "stable"


class DailyReport(BaseModel):
    """Daily automated report."""
    report_id: str
    date: datetime
    user_id: str
    
    # Publications summary
    posts_published: int
    official_posts: int
    satellite_posts: int
    
    # Performance
    total_views: int
    total_engagement: int
    avg_retention: float
    avg_ctr: float
    
    # Key metrics
    metrics: List[PerformanceMetric] = []
    
    # Top performers
    best_post_id: Optional[str] = None
    best_post_reason: Optional[str] = None
    worst_post_id: Optional[str] = None
    worst_post_reason: Optional[str] = None
    
    # Audience changes
    followers_change: int
    audience_growth_rate: float
    
    # Alerts
    alerts: List[str] = []
    
    # Strategic recommendations
    recommendations: List[str] = []
    
    # Tomorrow's focus
    tomorrow_focus: List[str] = []
    
    # Metadata
    generated_at: datetime
    generated_by: str = "community_ai"


# ========================================
# Community Manager Output
# ========================================

class CommunityManagerDecision(BaseModel):
    """Complete CM output."""
    decision_id: str
    timestamp: datetime
    
    # Plans
    official_plan: List[PostPlan] = []
    satellite_tests: List[PostPlan] = []
    
    # Recommendations
    creative_recommendations: List[CreativeRecommendation] = []
    videoclip_concepts: List[VideoclipRecommendation] = []
    
    # Insights
    trend_insights: List[str] = []
    aesthetic_recommendations: List[str] = []
    
    # Warnings
    warnings: List[str] = []
    
    # Overall confidence
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Cost
    estimated_cost_eur: float
    
    # Metadata
    brand_rules_version: str
    vision_metadata_used: bool
    satellite_data_used: bool
