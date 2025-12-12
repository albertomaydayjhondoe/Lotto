"""
SQLAlchemy models for Meta Creative Analyzer (PASO 10.15)
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class MetaCreativeAnalysisModel(Base):
    """
    Creative analysis results including performance metrics, scoring, and fatigue detection.
    """
    __tablename__ = "meta_creative_analysis"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Creative identification
    creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Performance metrics (JSONB for flexibility)
    metrics = Column(JSONB, nullable=False)  # CreativePerformanceMetrics
    
    # Scoring
    overall_score = Column(Float, nullable=False, default=0.0)
    performance_score = Column(Float, nullable=False, default=0.0)
    engagement_score = Column(Float, nullable=False, default=0.0)
    completion_score = Column(Float, nullable=True)
    fatigue_penalty = Column(Float, nullable=False, default=0.0)
    score_components = Column(JSONB, nullable=True)  # Detailed breakdown
    score_reasoning = Column(Text, nullable=True)
    
    # Fatigue detection
    is_fatigued = Column(Boolean, nullable=False, default=False, index=True)
    fatigue_score = Column(Float, nullable=True)
    fatigue_level = Column(String(20), nullable=True, index=True)  # healthy, mild, moderate, severe, critical
    fatigue_signals = Column(JSONB, nullable=True)  # List of FatigueSignal
    
    # Creative lifecycle
    days_active = Column(Integer, nullable=False, default=0)
    impressions_total = Column(Integer, nullable=False, default=0)
    
    # Recommendations
    recommendation = Column(Text, nullable=True)
    urgency = Column(String(20), nullable=True, index=True)  # low, medium, high, critical
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    processing_time_ms = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_creative_analysis_creative_analyzed', 'creative_id', 'analyzed_at'),
        Index('idx_creative_analysis_fatigued', 'is_fatigued', 'fatigue_level'),
        Index('idx_creative_analysis_score', 'overall_score'),
        Index('idx_creative_analysis_urgency', 'urgency'),
    )


class MetaCreativeVariantModel(Base):
    """
    Generated creative variants for recombination and testing.
    """
    __tablename__ = "meta_creative_variant"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Variant identification
    variant_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    base_creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variant_number = Column(Integer, nullable=False)
    
    # Variant details
    changes = Column(JSONB, nullable=False)  # List of VariantChange
    estimated_improvement = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.5)
    
    # Recombination metadata
    recombination_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    recombination_strategy = Column(String(50), nullable=True)
    
    # Performance tracking (if variant is tested)
    actual_performance = Column(JSONB, nullable=True)  # CreativePerformanceMetrics if tested
    performance_vs_base = Column(Float, nullable=True)  # Actual improvement %
    
    # Status
    status = Column(String(20), nullable=False, default="generated", index=True)  # generated, testing, approved, rejected
    tested = Column(Boolean, nullable=False, default=False)
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tested_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_variant_base_creative', 'base_creative_id', 'generated_at'),
        Index('idx_variant_recombination', 'recombination_id'),
        Index('idx_variant_status', 'status'),
        Index('idx_variant_tested', 'tested', 'tested_at'),
    )


class MetaCreativeHealthLogModel(Base):
    """
    Health check logs for tracking creative status over time.
    """
    __tablename__ = "meta_creative_health_log"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Creative identification
    creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Health status
    health_status = Column(String(20), nullable=False, index=True)  # healthy, warning, critical
    overall_score = Column(Float, nullable=False, default=0.0)
    
    # Fatigue tracking
    is_fatigued = Column(Boolean, nullable=False, default=False, index=True)
    fatigue_level = Column(String(20), nullable=True)
    fatigue_score = Column(Float, nullable=True)
    
    # Recommendations
    recommendation = Column(Text, nullable=True)
    recommendation_type = Column(String(50), nullable=True, index=True)  # refresh, pause, boost, optimize
    urgency = Column(String(20), nullable=True, index=True)
    
    # Actions taken (if any)
    actions_taken = Column(JSONB, nullable=True)  # List of actions
    auto_applied = Column(Boolean, nullable=False, default=False)
    
    # Snapshot of metrics at check time
    metrics_snapshot = Column(JSONB, nullable=True)
    
    # Processing metadata
    mode = Column(String(20), nullable=False, default="stub")
    processing_time_ms = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_health_log_creative_checked', 'creative_id', 'checked_at'),
        Index('idx_health_log_health_status', 'health_status', 'urgency'),
        Index('idx_health_log_fatigued', 'is_fatigued', 'fatigue_level'),
        Index('idx_health_log_recommendation', 'recommendation_type'),
    )
