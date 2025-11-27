"""
SQLAlchemy models for Meta Creative Optimizer (PASO 10.16)
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class MetaCreativeDecisionModel(Base):
    """
    Stores creative optimization decisions
    
    Tracks role assignments, recommended actions, budget decisions,
    and variant generation decisions for each creative.
    """
    __tablename__ = "meta_creative_decision"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    optimization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Role assignment
    assigned_role = Column(String(50), nullable=False)  # winner, test, fatigue, archive, pending
    previous_role = Column(String(50), nullable=True)
    role_changed = Column(Boolean, nullable=False, default=False)
    
    # Decision details
    recommended_actions = Column(JSONB, nullable=False)  # List[OptimizationAction]
    priority = Column(Integer, nullable=False)  # 1-5
    confidence = Column(String(20), nullable=False)  # high, medium, low
    reasoning = Column(Text, nullable=True)
    estimated_impact = Column(Float, nullable=True)  # Expected improvement %
    
    # Budget decisions
    current_budget = Column(Float, nullable=True)
    recommended_budget = Column(Float, nullable=True)
    budget_change_pct = Column(Float, nullable=True)
    
    # Variant decisions
    should_generate_variants = Column(Boolean, nullable=False, default=False)
    variant_strategy = Column(String(50), nullable=True)  # conservative, balanced, aggressive
    should_recombine = Column(Boolean, nullable=False, default=False)
    
    # Execution tracking
    actions_executed = Column(JSONB, nullable=True)  # List of executed actions
    execution_status = Column(String(50), nullable=True)  # pending, in_progress, completed, failed
    execution_errors = Column(JSONB, nullable=True)
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    processing_time_ms = Column(Integer, nullable=True)
    decided_at = Column(DateTime, nullable=False, server_default=func.now())
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_creative_decision_creative_decided', 'creative_id', 'decided_at'),
        Index('idx_creative_decision_campaign_decided', 'campaign_id', 'decided_at'),
        Index('idx_creative_decision_optimization', 'optimization_id', 'decided_at'),
        Index('idx_creative_decision_role', 'assigned_role', 'priority'),
        Index('idx_creative_decision_actions', 'should_generate_variants', 'should_recombine'),
        Index('idx_creative_decision_execution', 'execution_status', 'executed_at'),
    )


class MetaCreativeWinnerLogModel(Base):
    """
    Logs creative winner selections
    
    Tracks which creative was selected as winner, when, and performance metrics.
    Maintains historical record of all winner selections.
    """
    __tablename__ = "meta_creative_winner_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    optimization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Winner selection details
    winner_score = Column(Float, nullable=False)  # Composite score
    overall_score = Column(Float, nullable=False)  # From creative analyzer
    roas = Column(Float, nullable=False)
    ctr = Column(Float, nullable=False)
    cvr = Column(Float, nullable=False)
    spend = Column(Float, nullable=False)
    conversions = Column(Integer, nullable=False)
    
    # Runner-up info
    runner_up_creative_id = Column(UUID(as_uuid=True), nullable=True)
    runner_up_score = Column(Float, nullable=True)
    candidates_evaluated = Column(Integer, nullable=False)
    
    # Decision metadata
    confidence = Column(String(20), nullable=False)  # high, medium, low
    reasoning = Column(Text, nullable=True)
    
    # Performance tracking
    days_active = Column(Integer, nullable=False)
    days_as_winner = Column(Integer, nullable=False, default=0)
    previous_winner_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Status
    is_current_winner = Column(Boolean, nullable=False, default=True)
    replaced_at = Column(DateTime, nullable=True)
    replaced_by_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    processing_time_ms = Column(Integer, nullable=True)
    selected_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_winner_log_campaign_selected', 'campaign_id', 'selected_at'),
        Index('idx_winner_log_creative_selected', 'creative_id', 'selected_at'),
        Index('idx_winner_log_current', 'is_current_winner', 'campaign_id'),
        Index('idx_winner_log_score', 'winner_score', 'confidence'),
        Index('idx_winner_log_performance', 'roas', 'conversions'),
    )


class MetaCreativeOptimizationAuditModel(Base):
    """
    Audit log for optimization runs
    
    Tracks each optimization cycle execution with full details,
    decisions made, actions taken, and outcomes.
    """
    __tablename__ = "meta_creative_optimization_audit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    optimization_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # Scope
    campaign_ids = Column(JSONB, nullable=False)  # List[UUID]
    campaigns_processed = Column(Integer, nullable=False)
    creatives_processed = Column(Integer, nullable=False)
    
    # Results summary
    winners_selected = Column(Integer, nullable=False)
    decisions_made = Column(Integer, nullable=False)
    actions_recommended = Column(Integer, nullable=False)
    orchestrations_executed = Column(Integer, nullable=False)
    
    # Decision breakdown
    winners_count = Column(Integer, nullable=False, default=0)
    testers_count = Column(Integer, nullable=False, default=0)
    fatigued_count = Column(Integer, nullable=False, default=0)
    archived_count = Column(Integer, nullable=False, default=0)
    
    # Action breakdown
    promote_count = Column(Integer, nullable=False, default=0)
    scale_budget_count = Column(Integer, nullable=False, default=0)
    reduce_budget_count = Column(Integer, nullable=False, default=0)
    generate_variants_count = Column(Integer, nullable=False, default=0)
    recombine_count = Column(Integer, nullable=False, default=0)
    pause_count = Column(Integer, nullable=False, default=0)
    
    # Budget impact
    total_spend = Column(Float, nullable=False)
    total_budget_change = Column(Float, nullable=False, default=0.0)
    budget_scale_ups = Column(Integer, nullable=False, default=0)
    budget_scale_downs = Column(Integer, nullable=False, default=0)
    
    # Integration tracking
    data_sources_used = Column(JSONB, nullable=False)  # Dict[str, bool]
    orchestrator_calls = Column(Integer, nullable=False, default=0)
    orchestrator_successes = Column(Integer, nullable=False, default=0)
    orchestrator_failures = Column(Integer, nullable=False, default=0)
    
    # Errors
    errors = Column(JSONB, nullable=True)  # List of error messages
    warnings = Column(JSONB, nullable=True)  # List of warnings
    
    # Execution details
    execution_summary = Column(Text, nullable=True)
    trigger = Column(String(50), nullable=False)  # scheduler, manual, api
    triggered_by = Column(String(100), nullable=True)  # user_id or system
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    processing_time_ms = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_optimization_audit_started', 'started_at', 'mode'),
        Index('idx_optimization_audit_trigger', 'trigger', 'started_at'),
        Index('idx_optimization_audit_performance', 'campaigns_processed', 'processing_time_ms'),
        Index('idx_optimization_audit_results', 'winners_selected', 'decisions_made'),
        Index('idx_optimization_audit_errors', 'orchestrator_failures'),
    )
