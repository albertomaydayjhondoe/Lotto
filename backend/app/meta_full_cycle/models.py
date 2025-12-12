"""
Models para Meta Full Autonomous Cycle (PASO 10.11)
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MetaCycleRunModel(Base):
    """
    Registro de cada ejecución del ciclo autónomo completo.
    
    Almacena métricas, estado, duración y snapshot de estadísticas.
    """
    __tablename__ = "meta_cycle_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Duración en milisegundos
    
    # Status
    status = Column(String(50), nullable=False, default="running", index=True)
    # Values: "running", "success", "failed", "partial"
    
    # Steps executed
    steps_executed = Column(JSON, nullable=True)
    # Format: ["step_1_collection", "step_2_decisions", "step_3_api_actions", "step_4_logging"]
    
    # Errors
    errors = Column(JSON, nullable=True)
    # Format: [{"step": "step_2", "error": "...", "timestamp": "..."}]
    
    # Stats snapshot
    stats_snapshot = Column(JSON, nullable=True)
    # Format: {
    #   "campaigns_active": 10,
    #   "adsets_active": 50,
    #   "ads_active": 200,
    #   "total_spend_today": 1500.50,
    #   "avg_roas": 3.2,
    #   "ab_tests_active": 5,
    #   "spikes_detected": 3,
    #   "variants_generated": 12,
    #   "actions_taken": 8
    # }
    
    # Metadata
    triggered_by = Column(String(100), nullable=True)  # "scheduler", "manual", "api"
    mode = Column(String(20), nullable=False, default="stub")  # "stub" or "live"
    
    # Relationships
    action_logs = relationship("MetaCycleActionLogModel", back_populates="cycle_run", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetaCycleActionLogModel(Base):
    """
    Log detallado de cada acción/decisión tomada durante el ciclo.
    
    Permite auditar y debuggear el comportamiento del sistema autónomo.
    """
    __tablename__ = "meta_cycle_action_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to cycle run
    cycle_run_id = Column(UUID(as_uuid=True), ForeignKey("meta_cycle_runs.id"), nullable=False, index=True)
    
    # Step identification
    step = Column(String(100), nullable=False, index=True)
    # Values: "collection", "ab_decision", "roas_decision", "spike_decision", 
    #         "fatigue_detection", "api_action", "logging"
    
    action = Column(String(200), nullable=False)
    # Examples: "publish_ab_winner", "scale_budget_up_20", "pause_ad", "generate_variant"
    
    # Input/Output snapshots
    input_snapshot = Column(JSON, nullable=True)
    output_snapshot = Column(JSON, nullable=True)
    
    # Success/Error
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    entity_type = Column(String(50), nullable=True)  # "campaign", "adset", "ad", "creative"
    entity_id = Column(String(128), nullable=True, index=True)
    
    # Relationships
    cycle_run = relationship("MetaCycleRunModel", back_populates="action_logs")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# Indexes for performance
Index("idx_cycle_runs_status_started", MetaCycleRunModel.status, MetaCycleRunModel.started_at)
Index("idx_action_logs_cycle_step", MetaCycleActionLogModel.cycle_run_id, MetaCycleActionLogModel.step)
Index("idx_action_logs_entity", MetaCycleActionLogModel.entity_type, MetaCycleActionLogModel.entity_id)
