"""
Pydantic schemas for Meta Targeting Optimizer.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class GenderSplit(str, Enum):
    """Gender targeting options."""
    ALL = "all"
    MALE = "male"
    FEMALE = "female"


class SegmentType(str, Enum):
    """Segment classification."""
    INTEREST = "interest"
    BEHAVIOR = "behavior"
    DEMOGRAPHIC = "demographic"
    LOOKALIKE = "lookalike"
    CUSTOM_AUDIENCE = "custom_audience"
    PIXEL = "pixel"


class OptimizationStatus(str, Enum):
    """Optimization run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Segment Scoring Schemas
# ============================================================================

class SegmentMetrics(BaseModel):
    """Raw metrics for a segment."""
    model_config = ConfigDict(from_attributes=True)
    
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    spend: float = Field(default=0.0)
    revenue: float = Field(default=0.0)
    ctr: float = Field(default=0.0)
    cvr: float = Field(default=0.0)
    roas: float = Field(default=0.0)


class SegmentScore(BaseModel):
    """Computed score for a segment."""
    model_config = ConfigDict(from_attributes=True)
    
    segment_id: str
    segment_name: str
    segment_type: SegmentType
    
    # Raw metrics
    metrics: SegmentMetrics
    
    # Bayesian smoothed scores
    bayesian_ctr: float = Field(default=0.0)
    bayesian_cvr: float = Field(default=0.0)
    bayesian_roas: float = Field(default=0.0)
    
    # Weighted final score (CTR 25%, CVR 40%, ROAS 35%)
    composite_score: float = Field(default=0.0)
    
    # Confidence level (based on sample size)
    confidence: float = Field(default=0.0)
    
    # Ranking
    rank: Optional[int] = None
    
    # Blacklist flag
    is_fatigued: bool = Field(default=False)


# ============================================================================
# Geo Allocation Schemas
# ============================================================================

class GeoConstraint(BaseModel):
    """Geographic allocation constraints."""
    model_config = ConfigDict(from_attributes=True)
    
    country_code: str = Field(..., description="ISO 2-letter country code")
    min_budget_pct: float = Field(default=0.0, ge=0, le=100)
    max_budget_pct: float = Field(default=100.0, ge=0, le=100)
    priority: int = Field(default=5, ge=1, le=10)


class GeoAllocation(BaseModel):
    """Recommended budget allocation per country."""
    model_config = ConfigDict(from_attributes=True)
    
    country_code: str
    country_name: str
    budget_pct: float = Field(..., ge=0, le=100)
    budget_amount: float = Field(default=0.0)
    
    # Reasoning
    avg_cpc: float = Field(default=0.0)
    avg_ctr: float = Field(default=0.0)
    avg_roas: float = Field(default=0.0)
    engagement_score: float = Field(default=0.0)


# ============================================================================
# Audience Schemas
# ============================================================================

class LookalikeSpec(BaseModel):
    """Lookalike audience specification."""
    model_config = ConfigDict(from_attributes=True)
    
    source_audience_id: str
    country_codes: List[str]
    ratio: float = Field(default=0.01, ge=0.01, le=0.20)
    name: str
    description: Optional[str] = None


class CustomAudienceSpec(BaseModel):
    """Custom audience specification."""
    model_config = ConfigDict(from_attributes=True)
    
    audience_id: str
    name: str
    size: int = Field(default=0)
    description: Optional[str] = None


class InterestSpec(BaseModel):
    """Interest targeting specification."""
    model_config = ConfigDict(from_attributes=True)
    
    interest_id: str
    interest_name: str
    score: float
    rank: int


class BehaviorSpec(BaseModel):
    """Behavior targeting specification."""
    model_config = ConfigDict(from_attributes=True)
    
    behavior_id: str
    behavior_name: str
    score: float
    rank: int


# ============================================================================
# Targeting Recommendation Schemas
# ============================================================================

class TargetingRecommendation(BaseModel):
    """Complete targeting recommendation for an adset."""
    model_config = ConfigDict(from_attributes=True)
    
    adset_id: str
    campaign_id: str
    
    # Geographic
    countries: List[str] = Field(default_factory=list)
    geo_allocations: List[GeoAllocation] = Field(default_factory=list)
    
    # Demographic
    age_min: int = Field(default=18, ge=13, le=65)
    age_max: int = Field(default=65, ge=13, le=65)
    gender: GenderSplit = Field(default=GenderSplit.ALL)
    
    # Interests & Behaviors
    interests: List[InterestSpec] = Field(default_factory=list)
    behaviors: List[BehaviorSpec] = Field(default_factory=list)
    
    # Audiences
    custom_audiences: List[CustomAudienceSpec] = Field(default_factory=list)
    lookalikes: List[LookalikeSpec] = Field(default_factory=list)
    
    # Frequency control
    frequency_cap: int = Field(default=3, ge=1, le=10)
    frequency_window_days: int = Field(default=7, ge=1, le=90)
    
    # Budget per segment
    total_budget: float = Field(default=0.0)
    budget_per_segment: Dict[str, float] = Field(default_factory=dict)
    
    # Reasoning trace
    reasoning: Dict[str, Any] = Field(default_factory=dict)
    
    # Scores
    expected_ctr: float = Field(default=0.0)
    expected_cvr: float = Field(default=0.0)
    expected_roas: float = Field(default=0.0)
    confidence: float = Field(default=0.0)


# ============================================================================
# Optimization Run Schemas
# ============================================================================

class RunOptimizationRequest(BaseModel):
    """Request to run targeting optimization."""
    model_config = ConfigDict(from_attributes=True)
    
    campaign_id: Optional[str] = Field(default=None, description="Single campaign or all active")
    mode: str = Field(default="stub", pattern="^(stub|live)$")
    force_refresh: bool = Field(default=False)


class RunOptimizationResponse(BaseModel):
    """Response from optimization run."""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: str
    status: OptimizationStatus
    campaign_ids: List[str]
    recommendations_count: int
    duration_ms: int
    message: str


class ApplyTargetingRequest(BaseModel):
    """Request to apply targeting recommendation."""
    model_config = ConfigDict(from_attributes=True)
    
    recommendation_id: str
    mode: str = Field(default="stub", pattern="^(stub|live)$")
    dry_run: bool = Field(default=True)


class ApplyTargetingResponse(BaseModel):
    """Response from applying targeting."""
    model_config = ConfigDict(from_attributes=True)
    
    recommendation_id: str
    adset_id: str
    success: bool
    applied_changes: Dict[str, Any]
    message: str


# ============================================================================
# History & Analytics Schemas
# ============================================================================

class TargetingHistoryEntry(BaseModel):
    """Historical targeting change entry."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    run_id: str
    campaign_id: str
    adset_id: str
    applied_at: datetime
    
    old_targeting: Dict[str, Any]
    new_targeting: Dict[str, Any]
    
    # Performance before/after (collected later)
    before_ctr: Optional[float] = None
    before_cvr: Optional[float] = None
    before_roas: Optional[float] = None
    
    after_ctr: Optional[float] = None
    after_cvr: Optional[float] = None
    after_roas: Optional[float] = None
    
    success: bool
    error_message: Optional[str] = None


class SegmentPerformanceSummary(BaseModel):
    """Summary of segment performance."""
    model_config = ConfigDict(from_attributes=True)
    
    segment_id: str
    segment_name: str
    segment_type: SegmentType
    
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_spend: float
    total_revenue: float
    
    avg_ctr: float
    avg_cvr: float
    avg_roas: float
    
    campaigns_count: int
    last_used: Optional[datetime] = None
    
    is_fatigued: bool = Field(default=False)
    fatigue_reason: Optional[str] = None
