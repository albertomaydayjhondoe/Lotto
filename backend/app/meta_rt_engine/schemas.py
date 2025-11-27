"""
Pydantic schemas for Meta Real-Time Performance Engine (PASO 10.14)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# ENUMS
# ============================================================================

class ActionType(str, Enum):
    """Types of real-time actions"""
    PAUSE_AD = "pause_ad"
    PAUSE_ADSET = "pause_adset"
    PAUSE_CAMPAIGN = "pause_campaign"
    REDUCE_BUDGET = "reduce_budget"
    INCREASE_BUDGET = "increase_budget"
    RESET_BID = "reset_bid"
    TRIGGER_CREATIVE_RESYNC = "trigger_creative_resync"
    TRIGGER_FULL_CYCLE = "trigger_full_cycle"
    TRIGGER_TARGETING_REFRESH = "trigger_targeting_refresh"
    ALERT_ONLY = "alert_only"


class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    CTR_DROP = "ctr_drop"
    CVR_DROP = "cvr_drop"
    ROAS_COLLAPSE = "roas_collapse"
    CPM_SPIKE = "cpm_spike"
    SPEND_SPIKE = "spend_spike"
    FREQUENCY_SPIKE = "frequency_spike"
    DRIFT_DETECTED = "drift_detected"


class SeverityLevel(str, Enum):
    """Severity levels for anomalies"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# PERFORMANCE SNAPSHOT SCHEMAS
# ============================================================================

class PerformanceMetrics(BaseModel):
    """Current performance metrics"""
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    spend: float = Field(ge=0.0)
    ctr: float = Field(ge=0.0, le=1.0, description="Click-through rate (0-1)")
    cvr: float = Field(ge=0.0, le=1.0, description="Conversion rate (0-1)")
    cpm: float = Field(ge=0.0, description="Cost per 1000 impressions")
    cpc: float = Field(ge=0.0, description="Cost per click")
    cpa: float = Field(ge=0.0, description="Cost per acquisition")
    roas: float = Field(ge=0.0, description="Return on ad spend")
    frequency: float = Field(ge=1.0, description="Avg impressions per user")
    reach: int = Field(ge=0, description="Unique users reached")
    
    model_config = ConfigDict(from_attributes=True)


class PerformanceSnapshot(BaseModel):
    """Snapshot of campaign performance at a point in time"""
    campaign_id: UUID
    ad_account_id: str
    timestamp: datetime
    window_minutes: int = Field(default=5, description="Time window for metrics (5-30 min)")
    metrics: PerformanceMetrics
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class PerformanceSnapshotCreate(BaseModel):
    """Create performance snapshot request"""
    campaign_id: UUID
    ad_account_id: str
    window_minutes: int = Field(default=5, ge=1, le=60)
    
    model_config = ConfigDict(from_attributes=True)


class PerformanceSnapshotResponse(BaseModel):
    """Performance snapshot API response"""
    snapshot_id: UUID
    campaign_id: UUID
    timestamp: datetime
    metrics: PerformanceMetrics
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DETECTION SCHEMAS
# ============================================================================

class AnomalyDetection(BaseModel):
    """Detected anomaly in metrics"""
    anomaly_type: AnomalyType
    severity: SeverityLevel
    metric_name: str
    current_value: float
    baseline_value: float
    drop_percentage: Optional[float] = None
    spike_percentage: Optional[float] = None
    threshold_violated: float
    detection_timestamp: datetime
    confidence: float = Field(ge=0.0, le=1.0, default=0.95)
    description: str
    
    model_config = ConfigDict(from_attributes=True)


class DriftDetection(BaseModel):
    """Short-window drift detection result"""
    metric_name: str
    window_minutes: int
    mean_drift: float = Field(description="Mean drift from baseline")
    std_drift: float = Field(description="Standard deviation drift")
    is_drifting: bool
    drift_score: float = Field(ge=0.0, le=100.0, description="Drift severity 0-100")
    baseline_mean: float
    current_mean: float
    samples_analyzed: int
    
    model_config = ConfigDict(from_attributes=True)


class SpikeDetection(BaseModel):
    """Sudden spike detection in metrics"""
    metric_name: str
    spike_magnitude: float = Field(description="How many std devs from mean")
    current_value: float
    expected_value: float
    is_spike: bool
    spike_direction: str = Field(description="up or down")
    detection_time: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DetectionResult(BaseModel):
    """Complete detection result from RT-Detector"""
    campaign_id: UUID
    snapshot_id: UUID
    detection_timestamp: datetime
    anomalies: List[AnomalyDetection] = Field(default_factory=list)
    drifts: List[DriftDetection] = Field(default_factory=list)
    spikes: List[SpikeDetection] = Field(default_factory=list)
    has_critical_issues: bool
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    moderate_count: int = Field(ge=0)
    processing_time_ms: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DECISION SCHEMAS
# ============================================================================

class DecisionRule(BaseModel):
    """Rule that triggered a decision"""
    rule_id: str
    rule_name: str
    condition: str = Field(description="Human-readable condition")
    threshold: float
    actual_value: float
    matched: bool
    priority: int = Field(ge=1, le=10, default=5)
    
    model_config = ConfigDict(from_attributes=True)


class RealTimeDecision(BaseModel):
    """Decision made by RT Decision Engine"""
    decision_id: UUID
    campaign_id: UUID
    detection_result_id: UUID
    recommended_actions: List[ActionType]
    rules_triggered: List[DecisionRule]
    reasoning: str = Field(description="Why these actions were recommended")
    urgency: SeverityLevel
    should_auto_apply: bool = Field(default=False)
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DecisionResponse(BaseModel):
    """Decision API response"""
    decision_id: UUID
    campaign_id: UUID
    recommended_actions: List[ActionType]
    urgency: SeverityLevel
    reasoning: str
    rules_triggered: List[DecisionRule]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTION SCHEMAS
# ============================================================================

class ActionRequest(BaseModel):
    """Request to execute real-time action"""
    campaign_id: UUID
    action_type: ActionType
    decision_id: Optional[UUID] = None
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters (e.g., budget_reduction_pct)"
    )
    auto_apply: bool = Field(default=False, description="Execute immediately or only simulate")
    
    model_config = ConfigDict(from_attributes=True)


class ActionResult(BaseModel):
    """Result of a single action execution"""
    action_type: ActionType
    success: bool
    applied: bool = Field(description="Whether action was actually applied")
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int
    
    model_config = ConfigDict(from_attributes=True)


class ActionResponse(BaseModel):
    """Response from actions execution"""
    action_id: UUID
    campaign_id: UUID
    actions_executed: List[ActionResult]
    total_actions: int
    successful_actions: int
    failed_actions: int
    overall_success: bool
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LOG SCHEMAS
# ============================================================================

class RTLogEntry(BaseModel):
    """Single RT log entry"""
    log_id: UUID
    campaign_id: UUID
    log_type: str = Field(description="detection, decision, action, error")
    severity: SeverityLevel
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    snapshot_id: Optional[UUID] = None
    decision_id: Optional[UUID] = None
    action_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RTLogResponse(BaseModel):
    """RT logs API response"""
    logs: List[RTLogEntry]
    total: int
    page: int = 1
    page_size: int = 50
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API REQUEST/RESPONSE SCHEMAS
# ============================================================================

class RTRunRequest(BaseModel):
    """Request to run RT engine"""
    campaign_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Specific campaigns to check, or None for all active"
    )
    window_minutes: int = Field(default=5, ge=1, le=30)
    auto_apply_actions: bool = Field(default=False)
    detection_enabled: bool = Field(default=True)
    decisions_enabled: bool = Field(default=True)
    actions_enabled: bool = Field(default=False)
    
    model_config = ConfigDict(from_attributes=True)


class RTRunResponse(BaseModel):
    """Response from RT engine run"""
    run_id: UUID
    campaigns_analyzed: int
    snapshots_created: int
    anomalies_detected: int
    critical_anomalies: int
    decisions_made: int
    actions_executed: int
    duration_ms: int
    timestamp: datetime
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class RTHealthResponse(BaseModel):
    """RT Engine health check response"""
    status: str = Field(description="healthy, degraded, unhealthy")
    last_run: Optional[datetime] = None
    last_run_duration_ms: Optional[int] = None
    active_campaigns: int
    snapshots_last_hour: int
    anomalies_last_hour: int
    actions_last_hour: int
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of detector, decision_engine, actions"
    )
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RTLatestResponse(BaseModel):
    """Latest RT activity response"""
    campaign_id: UUID
    latest_snapshot: Optional[PerformanceSnapshotResponse] = None
    latest_detection: Optional[DetectionResult] = None
    latest_decision: Optional[DecisionResponse] = None
    latest_actions: List[ActionResult] = Field(default_factory=list)
    last_update: datetime
    
    model_config = ConfigDict(from_attributes=True)
