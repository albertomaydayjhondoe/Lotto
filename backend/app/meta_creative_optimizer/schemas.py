"""
Pydantic schemas for Meta Creative Optimizer (PASO 10.16)
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ==================== ENUMS ====================

class CreativeRole(str, Enum):
    """Role assigned to a creative"""
    WINNER = "winner"  # Current best performer
    TEST = "test"  # Under testing
    FATIGUE = "fatigue"  # Fatigued, needs refresh
    ARCHIVE = "archive"  # Retired
    PENDING = "pending"  # Not yet evaluated


class OptimizationAction(str, Enum):
    """Action to take on creative"""
    PROMOTE = "promote"  # Promote to winner
    SCALE_BUDGET = "scale_budget"  # Increase budget
    REDUCE_BUDGET = "reduce_budget"  # Decrease budget
    GENERATE_VARIANTS = "generate_variants"  # Generate new variants
    RECOMBINE = "recombine"  # Recombine fragments
    PAUSE = "pause"  # Pause creative
    ARCHIVE = "archive"  # Archive creative
    NO_ACTION = "no_action"  # No action needed


class DecisionConfidence(str, Enum):
    """Confidence level of decision"""
    HIGH = "high"  # >0.8
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"  # <0.5


# ==================== UNIFIED DATA MODELS ====================

class UnifiedCreativeData(BaseModel):
    """Unified data from all sources for a creative"""
    creative_id: UUID
    campaign_id: UUID
    
    # From Creative Analyzer (PASO 10.15)
    overall_score: float = Field(..., ge=0, le=100)
    performance_score: float = Field(..., ge=0, le=40)
    engagement_score: float = Field(..., ge=0, le=30)
    is_fatigued: bool
    fatigue_score: float = Field(..., ge=0, le=100)
    fatigue_level: str
    
    # From Insights Collector (PASO 10.7)
    ctr: float = Field(..., ge=0)
    cvr: float = Field(..., ge=0)
    cpc: float = Field(..., ge=0)
    cpm: float = Field(..., ge=0)
    roas: float = Field(..., ge=0)
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: int = Field(..., ge=0)
    spend: float = Field(..., ge=0)
    
    # From ROAS Engine (PASO 10.5)
    roas_efficiency: float = Field(..., ge=0)  # 0-100 score
    roas_trend: str  # "improving", "stable", "declining"
    
    # From Targeting Optimizer (PASO 10.12)
    target_score: Optional[float] = Field(None, ge=0, le=100)
    best_segments: Optional[List[str]] = None
    frequency_cap: Optional[float] = None
    
    # From Spike Manager (PASO 10.9)
    has_spike: bool = False
    spike_severity: Optional[str] = None
    
    # Metadata
    days_active: int = Field(..., ge=0)
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UnifiedCampaignData(BaseModel):
    """Unified data for entire campaign"""
    campaign_id: UUID
    total_creatives: int
    active_creatives: int
    total_spend: float
    total_conversions: int
    avg_roas: float
    avg_ctr: float
    avg_cvr: float
    best_creative_id: Optional[UUID] = None
    worst_creative_id: Optional[UUID] = None
    collected_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== WINNER SELECTION ====================

class WinnerCandidate(BaseModel):
    """Candidate for winner selection"""
    creative_id: UUID
    overall_score: float
    composite_score: float  # Weighted combination
    roas: float
    ctr: float
    cvr: float
    spend: float
    conversions: int
    days_active: int
    is_fatigued: bool
    confidence: float = Field(..., ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)


class WinnerSelectionResult(BaseModel):
    """Result of winner selection"""
    winner_creative_id: UUID
    winner_score: float
    candidates_evaluated: int
    runner_up_creative_id: Optional[UUID] = None
    runner_up_score: Optional[float] = None
    confidence: DecisionConfidence
    reasoning: str
    selected_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== CREATIVE DECISION ====================

class CreativeDecision(BaseModel):
    """Decision made for a creative"""
    creative_id: UUID
    assigned_role: CreativeRole
    previous_role: Optional[CreativeRole] = None
    recommended_actions: List[OptimizationAction]
    priority: int = Field(..., ge=1, le=5)  # 1=highest, 5=lowest
    confidence: DecisionConfidence
    reasoning: str
    estimated_impact: Optional[float] = None  # Expected improvement %
    
    # Budget decisions
    current_budget: Optional[float] = None
    recommended_budget: Optional[float] = None
    budget_change_pct: Optional[float] = None
    
    # Variant decisions
    should_generate_variants: bool = False
    variant_strategy: Optional[str] = None  # conservative, balanced, aggressive
    should_recombine: bool = False
    
    decided_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OptimizationDecisionResult(BaseModel):
    """Complete optimization decision for campaign"""
    campaign_id: UUID
    optimization_id: UUID
    winner: Optional[WinnerSelectionResult] = None
    decisions: List[CreativeDecision]
    total_creatives: int
    
    # Summary counts
    winners: int = 0
    testers: int = 0
    fatigued: int = 0
    archived: int = 0
    
    # Recommended actions summary
    promote_count: int = 0
    scale_budget_count: int = 0
    generate_variants_count: int = 0
    recombine_count: int = 0
    pause_count: int = 0
    
    total_spend: float
    total_budget_change: float = 0.0
    
    processing_time_ms: int
    decided_at: datetime
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)


# ==================== ORCHESTRATION ====================

class OrchestrationRequest(BaseModel):
    """Request to orchestrator for creative publication"""
    creative_id: UUID
    campaign_id: UUID
    action: str  # "publish", "update_budget", "create_adset"
    params: Dict[str, Any]
    priority: int = Field(3, ge=1, le=5)
    
    model_config = ConfigDict(from_attributes=True)


class OrchestrationResult(BaseModel):
    """Result from orchestrator"""
    success: bool
    request_id: Optional[UUID] = None
    creative_id: UUID
    action: str
    message: str
    meta_creative_id: Optional[str] = None
    executed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== API SCHEMAS ====================

class OptimizationStatusResponse(BaseModel):
    """Status response"""
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_campaigns: int
    total_creatives: int
    current_winner_count: int
    pending_decisions: int
    mode: str
    
    model_config = ConfigDict(from_attributes=True)


class RunOptimizationRequest(BaseModel):
    """Request to run optimization"""
    campaign_ids: Optional[List[UUID]] = None  # If None, run all
    force: bool = False
    mode: str = "stub"
    
    model_config = ConfigDict(from_attributes=True)


class RunOptimizationResponse(BaseModel):
    """Response after running optimization"""
    optimization_id: UUID
    campaigns_processed: int
    creatives_processed: int
    winners_selected: int
    decisions_made: int
    actions_recommended: int
    orchestrations_executed: int
    processing_time_ms: int
    summary: str
    started_at: datetime
    completed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CurrentWinnerResponse(BaseModel):
    """Current winner info"""
    campaign_id: UUID
    creative_id: UUID
    selected_at: datetime
    overall_score: float
    roas: float
    ctr: float
    cvr: float
    spend: float
    conversions: int
    days_as_winner: int
    confidence: DecisionConfidence
    
    model_config = ConfigDict(from_attributes=True)


class PromoteCreativeRequest(BaseModel):
    """Request to promote creative to winner"""
    force: bool = False
    reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PromoteCreativeResponse(BaseModel):
    """Response after promoting creative"""
    success: bool
    creative_id: UUID
    previous_role: CreativeRole
    new_role: CreativeRole
    previous_winner_id: Optional[UUID] = None
    message: str
    promoted_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    """Single recommendation"""
    creative_id: UUID
    campaign_id: UUID
    recommendation_type: OptimizationAction
    priority: int
    confidence: DecisionConfidence
    reasoning: str
    estimated_impact: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecommendationsResponse(BaseModel):
    """All recommendations"""
    total: int
    high_priority: int
    medium_priority: int
    low_priority: int
    recommendations: List[RecommendationItem]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    components: Dict[str, str]
    version: str = "1.0.0"
    mode: str
    
    model_config = ConfigDict(from_attributes=True)
