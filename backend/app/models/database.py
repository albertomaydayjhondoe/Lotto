"""
SQLAlchemy ORM models for database tables.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
import enum

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    RETRY = "retry"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipStatus(str, enum.Enum):
    """Clip status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class CampaignStatus(str, enum.Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class RuleStatus(str, enum.Enum):
    """Rule status enumeration."""
    CANDIDATE = "candidate"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


# Video Assets
class VideoAsset(Base):
    """Video asset model."""
    __tablename__ = "video_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    release_date = Column(DateTime, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clips = relationship("Clip", back_populates="video_asset")
    jobs = relationship("Job", back_populates="video_asset")


# Jobs
class Job(Base):
    """Job model for processing tasks."""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(String(50), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    params = Column(JSON, nullable=True)
    dedup_key = Column(String(255), unique=True, nullable=True)
    video_asset_id = Column(UUID(as_uuid=True), ForeignKey("video_assets.id"), nullable=True)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_asset = relationship("VideoAsset", back_populates="jobs")
    clip = relationship("Clip", back_populates="jobs", foreign_keys=[clip_id])


# Clips
class Clip(Base):
    """Clip model."""
    __tablename__ = "clips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_asset_id = Column(UUID(as_uuid=True), ForeignKey("video_assets.id"), nullable=False)
    start_ms = Column(Integer, nullable=False)
    end_ms = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    visual_score = Column(Float, nullable=True)
    status = Column(Enum(ClipStatus), default=ClipStatus.PENDING, nullable=False)
    params = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_asset = relationship("VideoAsset", back_populates="clips")
    variants = relationship("ClipVariant", back_populates="clip")
    jobs = relationship("Job", back_populates="clip", foreign_keys=[Job.clip_id])
    campaigns = relationship("Campaign", back_populates="clip")
    publications = relationship("Publication", back_populates="clip")


# Clip Variants
class ClipVariant(Base):
    """Clip variant model for platform-specific versions."""
    __tablename__ = "clip_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False)
    variant_number = Column(Integer, nullable=False)
    platform = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    status = Column(String(50), default="pending")
    params = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clip = relationship("Clip", back_populates="variants")


# Publications
class Publication(Base):
    """Publication tracking model."""
    __tablename__ = "publications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    post_url = Column(String(500), nullable=True)
    post_id = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    confirmed_by = Column(UUID(as_uuid=True), nullable=True)
    trace_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clip = relationship("Clip", back_populates="publications")


# Campaigns
class Campaign(Base):
    """Campaign model for ad campaigns."""
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False)
    budget_cents = Column(Integer, nullable=False)
    targeting = Column(JSON, nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clip = relationship("Clip", back_populates="campaigns")


# Platform Rules
class PlatformRule(Base):
    """Platform rules model."""
    __tablename__ = "platform_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    rules = Column(JSON, nullable=False)
    status = Column(Enum(RuleStatus), default=RuleStatus.CANDIDATE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Rule Engine Weights
class RuleEngineWeights(Base):
    """Rule engine weights model."""
    __tablename__ = "rules_engine_weights"
    
    platform = Column(String(50), primary_key=True)
    weights = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Best Clip Decisions (Campaigns Orchestrator)
class BestClipDecisionModel(Base):
    """Best clip decision model for campaigns orchestrator."""
    __tablename__ = "best_clip_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_asset_id = Column(UUID(as_uuid=True), ForeignKey("video_assets.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint on video_asset_id + platform
    __table_args__ = (
        UniqueConstraint('video_asset_id', 'platform', name='uq_video_asset_platform'),
    )
    
    # Relationships
    video_asset = relationship("VideoAsset", backref="best_clip_decisions")
    clip = relationship("Clip", backref="best_clip_decisions")
