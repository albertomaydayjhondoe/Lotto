"""
Pydantic schemas for AI Global Worker.

Defines data structures for:
- System snapshots
- AI reasoning outputs
- Recommendations and action plans
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SystemSnapshot(BaseModel):
    """Complete snapshot of system state at a point in time."""
    
    timestamp: datetime = Field(description="When snapshot was taken")
    
    # Queue metrics
    queue_pending: int = Field(description="Pending items in queue")
    queue_processing: int = Field(description="Items currently processing")
    queue_failed: int = Field(description="Failed queue items")
    queue_success: int = Field(description="Successful completions")
    
    # Scheduler metrics
    scheduler_pending: int = Field(description="Scheduled publications pending")
    scheduler_due_soon: int = Field(description="Publications due in next hour")
    
    # Orchestrator metrics
    orchestrator_running: bool = Field(description="Is orchestrator active")
    orchestrator_last_run: Optional[datetime] = Field(description="Last orchestrator execution")
    orchestrator_actions_last_24h: int = Field(description="Actions taken in last 24h")
    
    # Publishing metrics
    publish_success_rate: float = Field(description="Success rate (0.0 to 1.0)")
    publish_total_24h: int = Field(description="Total publications in 24h")
    publish_failed_24h: int = Field(description="Failed publications in 24h")
    
    # Content metrics
    clips_ready: int = Field(description="Clips ready to publish")
    clips_pending_analysis: int = Field(description="Clips awaiting analysis")
    jobs_pending: int = Field(description="Jobs in queue")
    jobs_failed: int = Field(description="Failed jobs")
    
    # Campaign metrics
    campaigns_active: int = Field(description="Active campaigns")
    campaigns_draft: int = Field(description="Draft campaigns")
    
    # Alert metrics
    alerts_critical: int = Field(description="Critical alerts")
    alerts_warning: int = Field(description="Warning alerts")
    
    # Platform-specific data
    platform_stats: Dict[str, Any] = Field(default_factory=dict, description="Per-platform metrics")
    
    # Best clips
    best_clips: Dict[str, Any] = Field(default_factory=dict, description="Best clip per platform")
    
    # Rule engine
    rule_weights: Dict[str, Any] = Field(default_factory=dict, description="Current rule weights")
    
    # Recent events
    recent_events: List[Dict[str, Any]] = Field(default_factory=list, description="Last 50 ledger events")
    
    # Additional context
    additional_metrics: Dict[str, Any] = Field(default_factory=dict, description="Extra metrics")


class AISummary(BaseModel):
    """AI-generated summary of system health and status."""
    
    overall_health: str = Field(description="Overall system health: excellent|good|warning|critical")
    health_score: float = Field(description="Health score 0-100")
    key_insights: List[str] = Field(description="3-5 key insights")
    concerns: List[str] = Field(description="Issues requiring attention")
    positives: List[str] = Field(description="Things going well")
    generated_at: datetime = Field(description="When summary was generated")


class AIRecommendation(BaseModel):
    """Single AI-generated recommendation."""
    
    id: str = Field(description="Unique recommendation ID")
    priority: str = Field(description="Priority: critical|high|medium|low")
    category: str = Field(description="Category: performance|content|campaigns|system")
    title: str = Field(description="Short recommendation title")
    description: str = Field(description="Detailed explanation")
    impact: str = Field(description="Expected impact if implemented")
    effort: str = Field(description="Effort required: low|medium|high")
    action_type: Optional[str] = Field(None, description="Action type if executable")
    action_payload: Optional[Dict[str, Any]] = Field(None, description="Parameters for action")


class AIActionPlan(BaseModel):
    """AI-generated action plan with steps."""
    
    plan_id: str = Field(description="Unique plan ID")
    title: str = Field(description="Plan title")
    objective: str = Field(description="What this plan aims to achieve")
    steps: List[Dict[str, Any]] = Field(description="Ordered steps to execute")
    estimated_duration: str = Field(description="Estimated time to complete")
    risk_level: str = Field(description="Risk level: low|medium|high")
    automated: bool = Field(description="Can this be automated?")


class AIReasoningOutput(BaseModel):
    """Complete AI reasoning output."""
    
    reasoning_id: str = Field(description="Unique reasoning ID")
    timestamp: datetime = Field(description="When reasoning was generated")
    snapshot: SystemSnapshot = Field(description="System snapshot used")
    summary: AISummary = Field(description="AI summary")
    recommendations: List[AIRecommendation] = Field(description="Prioritized recommendations")
    action_plan: AIActionPlan = Field(description="Proposed action plan")
    execution_time_ms: int = Field(description="Time taken to generate")


class AIRunResponse(BaseModel):
    """Response from manual AI reasoning trigger."""
    
    success: bool = Field(description="Was reasoning successful")
    reasoning_id: str = Field(description="ID of generated reasoning")
    message: str = Field(description="Status message")
    execution_time_ms: int = Field(description="Execution time")
