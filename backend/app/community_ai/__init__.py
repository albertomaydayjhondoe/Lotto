"""
Community Manager AI - Sprint 4B

Intelligent content planning and creative recommendations system.
"""

from .models import (
    # Enums
    ContentType,
    Platform,
    ChannelType,
    SentimentType,
    TrendCategory,
    
    # Planning
    PostPlan,
    DailyPlan,
    
    # Recommendations
    CreativeRecommendation,
    VideoclipRecommendation,
    
    # Trends
    TrendItem,
    TrendAnalysis,
    
    # Sentiment
    CommentAnalysis,
    SentimentReport,
    
    # Reports
    PerformanceMetric,
    DailyReport,
    
    # CM Output
    CommunityManagerDecision
)

from .planner import DailyPlanner
from .content_recommender import ContentRecommender
from .trend_miner import TrendMiner
from .sentiment_analyzer import SentimentAnalyzer
from .daily_reporter import DailyReporter

__all__ = [
    # Enums
    "ContentType",
    "Platform",
    "ChannelType",
    "SentimentType",
    "TrendCategory",
    
    # Models
    "PostPlan",
    "DailyPlan",
    "CreativeRecommendation",
    "VideoclipRecommendation",
    "TrendItem",
    "TrendAnalysis",
    "CommentAnalysis",
    "SentimentReport",
    "PerformanceMetric",
    "DailyReport",
    "CommunityManagerDecision",
    
    # Core classes
    "DailyPlanner",
    "ContentRecommender",
    "TrendMiner",
    "SentimentAnalyzer",
    "DailyReporter",
]

__version__ = "1.0.0"
