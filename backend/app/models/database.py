"""
SQLAlchemy ORM models for database tables.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Enum, LargeBinary
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


class PublishLogStatus(str, enum.Enum):
    """Publish log status enumeration."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


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


# Social Accounts (Publishing Engine)
class SocialAccountModel(Base):
    """Social media account model for publishing engine."""
    __tablename__ = "social_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform = Column(String(50), nullable=False)  # instagram, tiktok, youtube, other
    handle = Column(String(255), nullable=False)  # @stakazo, stakazo.oficial
    external_id = Column(String(255), nullable=True)  # Platform-specific account ID
    is_main_account = Column(Integer, nullable=False, default=0)  # SQLite-compatible boolean (0=False, 1=True)
    is_active = Column(Integer, nullable=False, default=1)  # SQLite-compatible boolean (0=False, 1=True)
    extra_metadata = Column(JSON, nullable=True)  # Additional account metadata
    
    # Secure credentials storage (PASO 5.1)
    encrypted_credentials = Column(LargeBinary, nullable=True)  # Encrypted credentials using Fernet
    credentials_version = Column(String(50), nullable=True)  # Encryption format version (e.g., "fernet-v1")
    credentials_updated_at = Column(DateTime, nullable=True)  # Last credentials update timestamp
    
    # OAuth tokens infrastructure (PASO 5.4)
    oauth_provider = Column(String(50), nullable=True)  # "instagram", "tiktok", "youtube", or other OAuth provider
    oauth_access_token = Column(Text, nullable=True)  # OAuth access token (can also use encrypted_credentials)
    oauth_refresh_token = Column(Text, nullable=True)  # OAuth refresh token for automatic renewal
    oauth_expires_at = Column(DateTime, nullable=True)  # UTC timestamp when access token expires
    oauth_scopes = Column(JSON, nullable=True)  # List of granted OAuth scopes (e.g., ["instagram_basic", "instagram_content_publish"])
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    publish_logs = relationship("PublishLogModel", back_populates="social_account")


# Publish Logs (Publishing Engine)
class PublishLogModel(Base):
    """Publication log model for tracking posts to social platforms."""
    __tablename__ = "publish_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # instagram, tiktok, youtube, other
    social_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, retry, success, failed
    external_post_id = Column(String(255), nullable=True)  # Platform-specific post ID
    external_url = Column(String(500), nullable=True)  # URL of the published post
    error_message = Column(Text, nullable=True)  # Error message if failed
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)  # When successfully published
    
    # Retry mechanism fields
    retry_count = Column(Integer, nullable=False, default=0)  # Number of retry attempts
    max_retries = Column(Integer, nullable=False, default=3)  # Maximum retry attempts
    last_retry_at = Column(DateTime, nullable=True)  # Last retry timestamp
    
    # Scheduling fields (PASO 4.4)
    schedule_type = Column(String(50), default="immediate")  # "immediate" or "scheduled"
    scheduled_for = Column(DateTime, nullable=True)  # When to publish (for scheduled posts)
    scheduled_window_end = Column(DateTime, nullable=True)  # End of scheduling window
    scheduled_by = Column(String(100), nullable=True)  # Who scheduled: "manual", "rule_engine", "campaign_orchestrator"
    
    extra_metadata = Column(JSON, nullable=True)  # Additional publication metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    clip = relationship("Clip", backref="publish_logs")
    social_account = relationship("SocialAccountModel", back_populates="publish_logs")


class AlertEventModel(Base):
    """Alert events table for alerting system."""
    __tablename__ = "alert_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    alert_metadata = Column("metadata", JSON, nullable=False, default={})  # Renamed to avoid conflict
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    read = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<AlertEvent(id={self.id}, type={self.alert_type}, severity={self.severity})>"


class UserModel(Base):
    """Users table for authentication and authorization."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.VIEWER.value)
    is_active = Column(Integer, nullable=False, default=1)  # SQLite compatible (1=True, 0=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class RefreshTokenModel(Base):
    """Refresh tokens table for JWT token management."""
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked = Column(Integer, nullable=False, default=0)  # SQLite compatible (1=True, 0=False)

    # Relationship
    user = relationship("UserModel", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={bool(self.revoked)})>"


class AIReasoningHistoryModel(Base):
    """AI Reasoning History - PASO 8.1
    
    Stores historical records of AI Global Worker reasoning runs for analysis and debugging.
    """
    __tablename__ = "ai_reasoning_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    run_id = Column(String(36), unique=True, nullable=False, index=True)  # reasoning_id from AIReasoningOutput
    triggered_by = Column(String(50), nullable=False)  # "worker", "manual", "debug"
    
    # Health metrics
    health_score = Column(Integer, nullable=False, index=True)  # 0-100
    status = Column(String(20), nullable=False, index=True)  # "ok", "degraded", "critical"
    critical_issues_count = Column(Integer, nullable=False, default=0)
    recommendations_count = Column(Integer, nullable=False, default=0)
    
    # Serialized data (JSON)
    snapshot_json = Column(JSON, nullable=True)
    summary_json = Column(JSON, nullable=True)
    recommendations_json = Column(JSON, nullable=True)
    action_plan_json = Column(JSON, nullable=True)
    
    # Performance
    duration_ms = Column(Integer, nullable=True)
    
    # Metadata
    meta = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AIReasoningHistory(id={self.id}, score={self.health_score}, status={self.status})>"
