"""
SQLAlchemy models for Meta Real-Time Performance Engine (PASO 10.14)
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class MetaPerformanceSnapshotModel(Base):
    """
    Performance snapshots captured every 5-15 minutes.
    Stores metrics for short-window drift and spike detection.
    """
    __tablename__ = "meta_performance_snapshot"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Campaign identification
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ad_account_id = Column(String(100), nullable=False, index=True)
    
    # Snapshot metadata
    snapshot_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    window_minutes = Column(Integer, nullable=False, default=5)  # Time window (5-30 min)
    
    # Performance metrics (stored as JSONB for flexibility)
    metrics = Column(JSONB, nullable=False)  # PerformanceMetrics dict
    
    # Metrics denormalized for fast queries
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversions = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    ctr = Column(Float, nullable=False, default=0.0)
    cvr = Column(Float, nullable=False, default=0.0)
    cpm = Column(Float, nullable=False, default=0.0)
    roas = Column(Float, nullable=False, default=0.0)
    
    # Metadata
    snapshot_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_snapshot_campaign_timestamp', 'campaign_id', 'snapshot_timestamp'),
        Index('idx_snapshot_account_timestamp', 'ad_account_id', 'snapshot_timestamp'),
        Index('idx_snapshot_ctr', 'ctr'),
        Index('idx_snapshot_roas', 'roas'),
        Index('idx_snapshot_created', 'created_at'),
    )


class MetaRealTimeLogModel(Base):
    """
    Real-time logs for detections, decisions, and actions.
    Comprehensive audit trail for all RT engine activity.
    """
    __tablename__ = "meta_realtime_log"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Campaign identification
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ad_account_id = Column(String(100), nullable=True, index=True)
    
    # Log classification
    log_type = Column(String(50), nullable=False, index=True)  # detection, decision, action, error
    severity = Column(String(20), nullable=False, index=True)  # low, moderate, high, critical
    
    # Log content
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)  # Flexible details storage
    
    # Relations to other entities
    snapshot_id = Column(UUID(as_uuid=True), nullable=True)  # FK to MetaPerformanceSnapshotModel
    decision_id = Column(UUID(as_uuid=True), nullable=True)
    action_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Detection results (if log_type == 'detection')
    anomalies_detected = Column(JSONB, nullable=True)  # List of AnomalyDetection
    drifts_detected = Column(JSONB, nullable=True)     # List of DriftDetection
    spikes_detected = Column(JSONB, nullable=True)     # List of SpikeDetection
    has_critical_issues = Column(Boolean, nullable=False, default=False)
    critical_count = Column(Integer, nullable=False, default=0)
    
    # Decision results (if log_type == 'decision')
    recommended_actions = Column(JSONB, nullable=True)  # List of ActionType
    rules_triggered = Column(JSONB, nullable=True)      # List of DecisionRule
    decision_reasoning = Column(Text, nullable=True)
    urgency = Column(String(20), nullable=True)
    should_auto_apply = Column(Boolean, nullable=True, default=False)
    
    # Action results (if log_type == 'action')
    actions_executed = Column(JSONB, nullable=True)     # List of ActionResult
    actions_successful = Column(Integer, nullable=True, default=0)
    actions_failed = Column(Integer, nullable=True, default=0)
    action_applied = Column(Boolean, nullable=True, default=False)
    
    # Processing metrics
    processing_time_ms = Column(Integer, nullable=True)
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_rtlog_campaign_timestamp', 'campaign_id', 'event_timestamp'),
        Index('idx_rtlog_type_severity', 'log_type', 'severity'),
        Index('idx_rtlog_critical', 'has_critical_issues', 'critical_count'),
        Index('idx_rtlog_snapshot', 'snapshot_id'),
        Index('idx_rtlog_decision', 'decision_id'),
        Index('idx_rtlog_created', 'created_at'),
    )
