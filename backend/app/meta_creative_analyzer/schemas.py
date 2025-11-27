"""
Pydantic schemas for Meta Creative Analyzer (PASO 10.15)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# Creative Performance Metrics
# ============================================================================

class CreativePerformanceMetrics(BaseModel):
    """Performance metrics for a creative."""
    model_config = ConfigDict(from_attributes=True)
    
    ctr: float = Field(..., description="Click-Through Rate")
    cvr: float = Field(..., description="Conversion Rate")
    cpc: float = Field(..., description="Cost Per Click")
    cpm: float = Field(..., description="Cost Per Mille")
    roas: float = Field(..., description="Return on Ad Spend")
    
    # Video completion rates
    video_3s: Optional[float] = Field(None, description="3-second video views %")
    video_10s: Optional[float] = Field(None, description="10-second video views %")
    video_25pct: Optional[float] = Field(None, description="25% completion rate")
    video_50pct: Optional[float] = Field(None, description="50% completion rate")
    video_75pct: Optional[float] = Field(None, description="75% completion rate")
    video_100pct: Optional[float] = Field(None, description="100% completion rate")
    
    # Engagement
    engagement_rate: float = Field(..., description="Overall engagement rate")
    impressions: int = Field(..., description="Total impressions")
    clicks: int = Field(..., description="Total clicks")
    conversions: int = Field(..., description="Total conversions")
    spend: float = Field(..., description="Total spend")


# ============================================================================
# Creative Scoring
# ============================================================================

class CreativeScore(BaseModel):
    """Unified creative scoring."""
    model_config = ConfigDict(from_attributes=True)
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall creative score 0-100")
    performance_score: float = Field(..., ge=0, le=100, description="Performance component")
    engagement_score: float = Field(..., ge=0, le=100, description="Engagement component")
    completion_score: Optional[float] = Field(None, ge=0, le=100, description="Video completion component")
    fatigue_penalty: float = Field(0.0, ge=0, le=50, description="Fatigue penalty 0-50")
    
    components: Dict[str, float] = Field(default_factory=dict, description="Score breakdown")
    reasoning: str = Field(..., description="Explanation of score")


# ============================================================================
# Fatigue Detection
# ============================================================================

class FatigueSignal(BaseModel):
    """Individual fatigue signal."""
    model_config = ConfigDict(from_attributes=True)
    
    metric: str = Field(..., description="Metric name (ctr, cvr, etc)")
    baseline_value: float = Field(..., description="Baseline value")
    current_value: float = Field(..., description="Current value")
    drop_pct: float = Field(..., description="Drop percentage")
    is_significant: bool = Field(..., description="Drop ≥30%?")


class FatigueDetectionResult(BaseModel):
    """Result of fatigue detection analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    is_fatigued: bool = Field(..., description="Is creative fatigued?")
    fatigue_score: float = Field(..., ge=0, le=100, description="Fatigue score 0-100")
    fatigue_level: str = Field(..., description="healthy, mild, moderate, severe, critical")
    
    signals: List[FatigueSignal] = Field(default_factory=list, description="Fatigue signals detected")
    days_active: int = Field(..., description="Days since creative was activated")
    impressions_total: int = Field(..., description="Total impressions to date")
    
    recommendation: str = Field(..., description="Action recommendation")
    urgency: str = Field(..., description="low, medium, high, critical")


# ============================================================================
# Creative Variants
# ============================================================================

class VariantChange(BaseModel):
    """Single change in a variant."""
    model_config = ConfigDict(from_attributes=True)
    
    change_type: str = Field(..., description="copy, title, thumbnail, fragment_order")
    original: str = Field(..., description="Original value")
    modified: str = Field(..., description="Modified value")
    reasoning: str = Field(..., description="Why this change was made")


class CreativeVariant(BaseModel):
    """Generated creative variant."""
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: UUID
    base_creative_id: UUID
    variant_number: int = Field(..., ge=1, description="Variant number (1-10)")
    
    changes: List[VariantChange] = Field(default_factory=list, description="List of changes")
    estimated_improvement: float = Field(..., description="Estimated improvement % vs base")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in variant 0-1")
    
    generated_at: datetime
    mode: str = Field("stub", description="stub or live")


# ============================================================================
# Recombination
# ============================================================================

class CreativeFragment(BaseModel):
    """Creative fragment for recombination."""
    model_config = ConfigDict(from_attributes=True)
    
    fragment_type: str = Field(..., description="intro, body, cta, outro")
    content: str = Field(..., description="Fragment content")
    performance_score: float = Field(..., ge=0, le=100, description="Fragment performance")
    usage_count: int = Field(0, description="Times used in campaigns")


class RecombinationResult(BaseModel):
    """Result of creative recombination."""
    model_config = ConfigDict(from_attributes=True)
    
    recombination_id: UUID
    base_creative_ids: List[UUID] = Field(..., description="Source creatives")
    generated_variants: List[CreativeVariant] = Field(default_factory=list)
    
    best_fragments: Dict[str, CreativeFragment] = Field(default_factory=dict)
    recombination_strategy: str = Field(..., description="Strategy used")
    
    total_variants: int = Field(..., description="Number of variants generated")
    processing_time_ms: int = Field(..., description="Processing time")


# ============================================================================
# API Request/Response Schemas
# ============================================================================

class AnalyzeCreativeRequest(BaseModel):
    """Request to analyze a creative."""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    include_fatigue_check: bool = Field(True, description="Check for fatigue")
    include_scoring: bool = Field(True, description="Calculate scores")
    mode: str = Field("stub", description="stub or live")


class AnalyzeCreativeResponse(BaseModel):
    """Response from creative analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    analysis_id: UUID
    creative_id: UUID
    
    metrics: CreativePerformanceMetrics
    score: CreativeScore
    fatigue: Optional[FatigueDetectionResult] = None
    
    analyzed_at: datetime
    processing_time_ms: int


class CreativeHealthResponse(BaseModel):
    """Creative health status."""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    health_status: str = Field(..., description="healthy, warning, critical")
    overall_score: float = Field(..., ge=0, le=100)
    
    is_fatigued: bool
    fatigue_level: str
    recommendation: str
    
    last_checked: datetime


class RecombineRequest(BaseModel):
    """Request to recombine creatives."""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    num_variants: int = Field(5, ge=1, le=10, description="Number of variants to generate")
    strategy: str = Field("balanced", description="aggressive, balanced, conservative")
    mode: str = Field("stub", description="stub or live")


class RecombineResponse(BaseModel):
    """Response from recombination."""
    model_config = ConfigDict(from_attributes=True)
    
    recombination_id: UUID
    creative_id: UUID
    variants: List[CreativeVariant]
    
    total_variants: int
    best_variant_id: UUID
    processing_time_ms: int


class RefreshAllRequest(BaseModel):
    """Request to refresh all fatigued creatives."""
    model_config = ConfigDict(from_attributes=True)
    
    fatigue_threshold: float = Field(60.0, ge=0, le=100, description="Fatigue score threshold")
    auto_apply: bool = Field(False, description="Auto-apply recommendations")
    mode: str = Field("stub", description="stub or live")


class RefreshAllResponse(BaseModel):
    """Response from refresh all."""
    model_config = ConfigDict(from_attributes=True)
    
    total_analyzed: int
    fatigued_count: int
    refreshed_count: int
    
    fatigued_creatives: List[UUID] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    processing_time_ms: int


class CreativeRecommendation(BaseModel):
    """Creative improvement recommendation."""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    recommendation_type: str = Field(..., description="refresh, pause, boost, optimize")
    urgency: str = Field(..., description="low, medium, high, critical")
    
    current_score: float
    expected_improvement: float
    
    actions: List[str] = Field(default_factory=list, description="Recommended actions")
    reasoning: str = Field(..., description="Why this recommendation")
    
    created_at: datetime


class RecommendationsResponse(BaseModel):
    """Response with all recommendations."""
    model_config = ConfigDict(from_attributes=True)
    
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    
    recommendations: List[CreativeRecommendation] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field("healthy", description="healthy or unhealthy")
    components: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime
