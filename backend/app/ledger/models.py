"""
Ledger models for event tracking and auditing.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, JSON, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class EventSeverity(str, enum.Enum):
    """Event severity levels."""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class LedgerEvent(Base):
    """
    Ledger event model for comprehensive system auditing.
    
    Records all important system actions in a queryable, traceable format
    for learning, optimization, anomaly detection, and AI context.
    """
    __tablename__ = "ledger_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    event_data = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    severity = Column(Enum(EventSeverity), default=EventSeverity.INFO, nullable=False)
    worker_id = Column(String(100), nullable=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    clip_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Composite index for entity lookups
    __table_args__ = (
        Index('idx_entity_lookup', 'entity_type', 'entity_id'),
    )
    
    def __repr__(self):
        return f"<LedgerEvent(id={self.id}, event_type={self.event_type}, entity={self.entity_type}:{self.entity_id})>"
