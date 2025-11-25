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


# ============================================================================
# META ADS MODELS - PASO 10.1
# ============================================================================


class MetaAccountModel(Base):
    """Meta (Facebook) Ads Account - PASO 10.1
    
    Stores Meta Business Manager accounts linked to social accounts.
    One-to-one relationship with SocialAccountModel (platform='facebook' or 'instagram').
    """
    __tablename__ = "meta_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    social_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id"), nullable=False, unique=True)
    
    # Meta account details
    ad_account_id = Column(String(255), nullable=False, unique=True, index=True)  # e.g., "act_123456789"
    business_id = Column(String(255), nullable=True, index=True)  # Meta Business Manager ID
    account_name = Column(String(255), nullable=True)
    currency = Column(String(10), nullable=True, default="USD")  # USD, EUR, etc.
    timezone = Column(String(50), nullable=True, default="UTC")
    
    # Account status
    is_active = Column(Integer, nullable=False, default=1)  # SQLite-compatible boolean
    account_status = Column(String(50), nullable=True)  # ACTIVE, DISABLED, etc.
    
    # Spending limits
    spend_cap = Column(Float, nullable=True)  # Max spend in account currency
    amount_spent = Column(Float, nullable=True, default=0.0)  # Total spent
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    social_account = relationship("SocialAccountModel", backref="meta_account")
    pixels = relationship("MetaPixelModel", back_populates="meta_account", cascade="all, delete-orphan")
    campaigns = relationship("MetaCampaignModel", back_populates="meta_account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaAccount(id={self.id}, ad_account_id={self.ad_account_id})>"


class MetaPixelModel(Base):
    """Meta Pixel - PASO 10.1
    
    Tracks Meta Pixel IDs for conversion tracking and audience building.
    """
    __tablename__ = "meta_pixels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    meta_account_id = Column(UUID(as_uuid=True), ForeignKey("meta_accounts.id"), nullable=False, index=True)
    
    # Pixel details
    pixel_id = Column(String(255), nullable=False, unique=True, index=True)
    pixel_name = Column(String(255), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)  # SQLite-compatible boolean
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    meta_account = relationship("MetaAccountModel", back_populates="pixels")
    
    def __repr__(self):
        return f"<MetaPixel(id={self.id}, pixel_id={self.pixel_id})>"


class MetaCreativeModel(Base):
    """Meta Creative - PASO 10.1
    
    Stores creative assets (videos, images) uploaded to Meta.
    Linked to VideoAsset for source video tracking.
    """
    __tablename__ = "meta_creatives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    video_asset_id = Column(UUID(as_uuid=True), ForeignKey("video_assets.id"), nullable=True, index=True)
    
    # Meta creative details
    creative_id = Column(String(255), nullable=False, unique=True, index=True)  # Meta's creative ID
    creative_name = Column(String(255), nullable=True)
    creative_type = Column(String(50), nullable=False)  # "video", "image", "carousel"
    
    # Video-specific fields
    video_url = Column(Text, nullable=True)  # Meta's hosted video URL
    thumbnail_url = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="active")  # active, archived, deleted
    
    # Human control flags
    is_approved = Column(Integer, nullable=False, default=0)  # Requires human approval
    is_reviewed = Column(Integer, nullable=False, default=0)  # Has been reviewed
    reviewed_by = Column(String(255), nullable=True)  # User who reviewed
    reviewed_at = Column(DateTime, nullable=True)
    
    # Content restrictions
    genre = Column(String(100), nullable=True)  # Content genre
    subgenre = Column(String(100), nullable=True)  # Content subgenre
    age_restriction = Column(String(20), nullable=True)  # "18+", "13+", "all"
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    video_asset = relationship("VideoAsset", backref="meta_creatives")
    ads = relationship("MetaAdModel", back_populates="creative")
    
    def __repr__(self):
        return f"<MetaCreative(id={self.id}, creative_id={self.creative_id}, type={self.creative_type})>"


class MetaCampaignModel(Base):
    """Meta Campaign - PASO 10.1
    
    Top-level campaign structure in Meta Ads hierarchy.
    Campaign → Adset → Ad → Insights
    """
    __tablename__ = "meta_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    meta_account_id = Column(UUID(as_uuid=True), ForeignKey("meta_accounts.id"), nullable=False, index=True)
    
    # Meta campaign details
    campaign_id = Column(String(255), nullable=False, unique=True, index=True)  # Meta's campaign ID
    campaign_name = Column(String(255), nullable=False)
    objective = Column(String(100), nullable=False)  # REACH, VIDEO_VIEWS, CONVERSIONS, etc.
    status = Column(String(50), nullable=False, default="PAUSED", index=True)  # ACTIVE, PAUSED, DELETED
    
    # Budget
    daily_budget = Column(Float, nullable=True)  # Daily budget in account currency
    lifetime_budget = Column(Float, nullable=True)  # Total lifetime budget
    budget_remaining = Column(Float, nullable=True)
    
    # Schedule
    start_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime, nullable=True)
    
    # Human control flags
    requires_approval = Column(Integer, nullable=False, default=1)  # Must be approved before activation
    is_approved = Column(Integer, nullable=False, default=0)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Tracking
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    meta_account = relationship("MetaAccountModel", back_populates="campaigns")
    adsets = relationship("MetaAdsetModel", back_populates="campaign", cascade="all, delete-orphan")
    ab_tests = relationship("MetaAbTestModel", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaCampaign(id={self.id}, name={self.campaign_name}, status={self.status})>"


class MetaAdsetModel(Base):
    """Meta Adset - PASO 10.1
    
    Mid-level adset structure in Meta Ads hierarchy.
    Contains targeting, budget, and schedule details.
    """
    __tablename__ = "meta_adsets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("meta_campaigns.id"), nullable=False, index=True)
    
    # Meta adset details
    adset_id = Column(String(255), nullable=False, unique=True, index=True)  # Meta's adset ID
    adset_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PAUSED", index=True)  # ACTIVE, PAUSED, DELETED
    
    # Budget (at adset level)
    daily_budget = Column(Float, nullable=True)
    lifetime_budget = Column(Float, nullable=True)
    bid_amount = Column(Float, nullable=True)
    bid_strategy = Column(String(50), nullable=True)  # LOWEST_COST_WITHOUT_CAP, COST_CAP, etc.
    
    # Targeting
    targeting = Column(JSON, nullable=True)  # Age, gender, location, interests, etc.
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # "male", "female", "all"
    locations = Column(JSON, nullable=True)  # Countries, cities, regions
    interests = Column(JSON, nullable=True)  # Interest targeting
    
    # Placement
    placements = Column(JSON, nullable=True)  # Facebook, Instagram, Audience Network, etc.
    
    # Schedule
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Optimization
    optimization_goal = Column(String(100), nullable=True)  # IMPRESSIONS, REACH, VIDEO_VIEWS, etc.
    billing_event = Column(String(50), nullable=True)  # IMPRESSIONS, VIDEO_VIEWS, etc.
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    campaign = relationship("MetaCampaignModel", back_populates="adsets")
    ads = relationship("MetaAdModel", back_populates="adset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaAdset(id={self.id}, name={self.adset_name}, status={self.status})>"


class MetaAdModel(Base):
    """Meta Ad - PASO 10.1
    
    Individual ad in Meta Ads hierarchy.
    Links creative to campaign/adset structure.
    """
    __tablename__ = "meta_ads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    adset_id = Column(UUID(as_uuid=True), ForeignKey("meta_adsets.id"), nullable=False, index=True)
    creative_id = Column(UUID(as_uuid=True), ForeignKey("meta_creatives.id"), nullable=True, index=True)
    
    # Meta ad details
    ad_id = Column(String(255), nullable=False, unique=True, index=True)  # Meta's ad ID
    ad_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PAUSED", index=True)  # ACTIVE, PAUSED, DELETED
    
    # Ad copy
    headline = Column(String(500), nullable=True)
    primary_text = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    call_to_action = Column(String(50), nullable=True)  # LEARN_MORE, SHOP_NOW, etc.
    
    # Landing page
    link_url = Column(Text, nullable=True)
    display_link = Column(String(255), nullable=True)
    
    # Pixel tracking
    pixel_id = Column(String(255), nullable=True, index=True)  # Pixel ID for conversion tracking
    
    # Human review
    is_reviewed = Column(Integer, nullable=False, default=0)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    adset = relationship("MetaAdsetModel", back_populates="ads")
    creative = relationship("MetaCreativeModel", back_populates="ads")
    insights = relationship("MetaAdInsightsModel", back_populates="ad", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaAd(id={self.id}, name={self.ad_name}, status={self.status})>"


class MetaAdInsightsModel(Base):
    """Meta Ad Insights - PASO 10.1
    
    Stores daily performance metrics for Meta ads.
    Time-series data for analysis and optimization.
    """
    __tablename__ = "meta_ad_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ad_id = Column(UUID(as_uuid=True), ForeignKey("meta_ads.id"), nullable=False, index=True)
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)  # Date of metrics (UTC)
    date_start = Column(DateTime, nullable=True)
    date_stop = Column(DateTime, nullable=True)
    
    # Delivery metrics
    impressions = Column(Integer, nullable=True, default=0)
    reach = Column(Integer, nullable=True, default=0)
    frequency = Column(Float, nullable=True, default=0.0)
    
    # Engagement metrics
    clicks = Column(Integer, nullable=True, default=0)
    inline_link_clicks = Column(Integer, nullable=True, default=0)
    unique_clicks = Column(Integer, nullable=True, default=0)
    ctr = Column(Float, nullable=True, default=0.0)  # Click-through rate
    
    # Video metrics
    video_views = Column(Integer, nullable=True, default=0)
    video_views_3s = Column(Integer, nullable=True, default=0)
    video_views_10s = Column(Integer, nullable=True, default=0)
    video_views_25_percent = Column(Integer, nullable=True, default=0)
    video_views_50_percent = Column(Integer, nullable=True, default=0)
    video_views_75_percent = Column(Integer, nullable=True, default=0)
    video_views_100_percent = Column(Integer, nullable=True, default=0)
    video_avg_watch_time = Column(Float, nullable=True, default=0.0)  # Seconds
    
    # Cost metrics
    spend = Column(Float, nullable=True, default=0.0)
    cpc = Column(Float, nullable=True, default=0.0)  # Cost per click
    cpm = Column(Float, nullable=True, default=0.0)  # Cost per thousand impressions
    cpp = Column(Float, nullable=True, default=0.0)  # Cost per purchase
    
    # Conversion metrics
    actions = Column(JSON, nullable=True)  # List of actions (likes, comments, shares, conversions)
    conversions = Column(Integer, nullable=True, default=0)
    conversion_rate = Column(Float, nullable=True, default=0.0)
    cost_per_conversion = Column(Float, nullable=True, default=0.0)
    
    # ROAS (Return on Ad Spend)
    purchase_value = Column(Float, nullable=True, default=0.0)
    roas = Column(Float, nullable=True, default=0.0)
    
    # Attribution
    attribution_setting = Column(String(50), nullable=True)  # "1d_view", "7d_click", etc.
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ad = relationship("MetaAdModel", back_populates="insights")
    
    # Composite unique constraint (one insight per ad per day)
    __table_args__ = (
        UniqueConstraint('ad_id', 'date', name='uq_meta_insights_ad_date'),
    )
    
    def __repr__(self):
        return f"<MetaAdInsights(ad_id={self.ad_id}, date={self.date}, impressions={self.impressions})>"


# Meta A/B Testing Model (PASO 10.4)
class MetaAbTestModel(Base):
    """A/B testing model for Meta Ads campaigns."""
    __tablename__ = "meta_ab_tests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("meta_campaigns.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String(255), nullable=False)
    
    # Test variants (list of clip IDs)
    variants = Column(JSON, nullable=False)  # [{"clip_id": "uuid", "ad_id": "uuid", "creative_id": "uuid"}]
    
    # Metrics to evaluate
    metrics = Column(JSON, nullable=False, default=["ctr", "cpc", "engagement"])  # List of metric names
    
    # Test status
    status = Column(String(50), nullable=False, default="active")  # active, evaluating, completed, archived, needs_more_data
    
    # Winner information
    winner_clip_id = Column(UUID(as_uuid=True), nullable=True)
    winner_ad_id = Column(UUID(as_uuid=True), nullable=True)
    winner_decided_at = Column(DateTime, nullable=True)
    
    # Metrics snapshot at evaluation time
    metrics_snapshot = Column(JSON, nullable=True)  # Snapshot of all metrics when winner was decided
    
    # Statistical evaluation results
    statistical_results = Column(JSON, nullable=True)  # Chi-square, p-values, confidence intervals
    
    # Test timing
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    min_impressions = Column(Integer, nullable=False, default=1000)  # Minimum impressions before evaluation
    min_duration_hours = Column(Integer, nullable=False, default=48)  # Minimum test duration in hours
    
    # Publishing information
    published_to_social = Column(Integer, nullable=False, default=0)  # 0=not published, 1=published
    publish_log_id = Column(UUID(as_uuid=True), ForeignKey("publish_logs.id"), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    campaign = relationship("MetaCampaignModel", back_populates="ab_tests")
    publish_log = relationship("PublishLogModel", foreign_keys=[publish_log_id])
    
    def __repr__(self):
        return f"<MetaAbTest(id={self.id}, test_name={self.test_name}, status={self.status})>"


class MetaPixelOutcomeModel(Base):
    """
    Pixel-based conversion outcomes from Meta Pixel events.
    
    Tracks user actions on landing pages/websites after clicking ads.
    Used for ROAS calculation and conversion attribution.
    """
    __tablename__ = "meta_pixel_outcomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Pixel and event information
    pixel_id = Column(String(255), nullable=False, index=True)
    event_id = Column(String(255), nullable=True, unique=True)  # Deduplication
    event_name = Column(String(100), nullable=False, index=True)  # ViewContent, AddToCart, Purchase, Lead, etc.
    
    # Ad attribution
    ad_id = Column(UUID(as_uuid=True), ForeignKey("meta_ads.id"), nullable=True, index=True)
    adset_id = Column(UUID(as_uuid=True), ForeignKey("meta_adsets.id"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("meta_campaigns.id"), nullable=False, index=True)
    
    # Conversion details
    conversion_type = Column(String(100), nullable=False, index=True)  # add_to_cart, purchase, lead, signup, etc.
    value_usd = Column(Float, nullable=True, default=0.0)  # Conversion value in USD
    currency = Column(String(10), nullable=True, default="USD")
    quantity = Column(Integer, nullable=True, default=1)
    
    # Session information
    session_id = Column(String(255), nullable=True, index=True)
    session_duration_seconds = Column(Integer, nullable=True)
    landing_path = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Device and location
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    platform = Column(String(50), nullable=True)  # ios, android, web
    country = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    
    # UTM tracking
    utm_source = Column(String(255), nullable=True, index=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True, index=True)
    utm_content = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    
    # Attribution and confidence
    attribution_model = Column(String(50), nullable=False, default="last_click")  # last_click, first_click, linear, time_decay
    attribution_weight = Column(Float, nullable=False, default=1.0)  # 0.0 to 1.0 for multi-touch attribution
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0 probability that this is a real conversion
    
    # Timing
    event_timestamp = Column(DateTime, nullable=False, index=True)
    click_timestamp = Column(DateTime, nullable=True)  # Time of ad click
    time_to_conversion_seconds = Column(Integer, nullable=True)  # Time from click to conversion
    
    # Metadata
    extra_data = Column(JSON, nullable=True)  # Additional pixel data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ad = relationship("MetaAdModel", foreign_keys=[ad_id])
    adset = relationship("MetaAdsetModel", foreign_keys=[adset_id])
    campaign = relationship("MetaCampaignModel", foreign_keys=[campaign_id])
    
    def __repr__(self):
        return f"<MetaPixelOutcome(id={self.id}, event={self.event_name}, value=${self.value_usd})>"


class MetaConversionEventModel(Base):
    """
    Aggregated conversion events per ad/adset/campaign.
    
    Provides pre-computed conversion metrics for faster ROAS calculations.
    Updated periodically from MetaPixelOutcomeModel.
    """
    __tablename__ = "meta_conversion_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Ad hierarchy
    ad_id = Column(UUID(as_uuid=True), ForeignKey("meta_ads.id"), nullable=True, index=True)
    adset_id = Column(UUID(as_uuid=True), ForeignKey("meta_adsets.id"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("meta_campaigns.id"), nullable=False, index=True)
    
    # Date range for aggregation
    date = Column(DateTime, nullable=False, index=True)  # Aggregation date (daily)
    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    
    # Conversion metrics
    total_conversions = Column(Integer, nullable=False, default=0)
    total_revenue_usd = Column(Float, nullable=False, default=0.0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)  # From insights
    
    # Conversion breakdown by type
    purchases = Column(Integer, nullable=False, default=0)
    leads = Column(Integer, nullable=False, default=0)
    add_to_carts = Column(Integer, nullable=False, default=0)
    view_contents = Column(Integer, nullable=False, default=0)
    initiates_checkout = Column(Integer, nullable=False, default=0)
    
    # Revenue breakdown
    purchase_revenue_usd = Column(Float, nullable=False, default=0.0)
    lead_value_usd = Column(Float, nullable=False, default=0.0)  # Estimated lead value
    
    # Calculated metrics
    conversion_rate = Column(Float, nullable=True)  # conversions / clicks
    cost_per_conversion = Column(Float, nullable=True)  # cost / conversions
    roas = Column(Float, nullable=True)  # revenue / cost
    average_order_value = Column(Float, nullable=True)  # revenue / purchases
    
    # Session metrics
    average_session_duration = Column(Float, nullable=True)  # Average in seconds
    bounce_rate = Column(Float, nullable=True)  # % of single-page sessions
    
    # Metadata
    extra_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ad = relationship("MetaAdModel", foreign_keys=[ad_id])
    adset = relationship("MetaAdsetModel", foreign_keys=[adset_id])
    campaign = relationship("MetaCampaignModel", foreign_keys=[campaign_id])
    
    # Unique constraint: one record per ad/adset/campaign per day
    __table_args__ = (
        UniqueConstraint('ad_id', 'date', name='uix_conversion_ad_date'),
        UniqueConstraint('adset_id', 'date', name='uix_conversion_adset_date'),
        UniqueConstraint('campaign_id', 'date', name='uix_conversion_campaign_date'),
    )
    
    def __repr__(self):
        return f"<MetaConversionEvent(id={self.id}, conversions={self.total_conversions}, roas={self.roas})>"


class MetaROASMetricsModel(Base):
    """
    Advanced ROAS metrics with predictions and optimization recommendations.
    
    Combines insights data with pixel outcomes to provide:
    - Real ROAS (from actual conversions)
    - Predicted ROAS (from ML models)
    - Optimization recommendations
    - Statistical confidence intervals
    """
    __tablename__ = "meta_roas_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Ad hierarchy
    ad_id = Column(UUID(as_uuid=True), ForeignKey("meta_ads.id"), nullable=True, index=True)
    adset_id = Column(UUID(as_uuid=True), ForeignKey("meta_adsets.id"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("meta_campaigns.id"), nullable=False, index=True)
    
    # Calculation period
    date = Column(DateTime, nullable=False, index=True)
    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    calculation_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Core ROAS metrics
    actual_roas = Column(Float, nullable=True)  # Real ROAS from pixel outcomes
    predicted_roas = Column(Float, nullable=True)  # ML-predicted ROAS
    blended_roas = Column(Float, nullable=True)  # Weighted combination
    
    # Revenue and cost
    total_revenue_usd = Column(Float, nullable=False, default=0.0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)
    expected_revenue_usd = Column(Float, nullable=True)  # Predicted revenue
    
    # Conversion metrics
    total_conversions = Column(Integer, nullable=False, default=0)
    conversion_rate = Column(Float, nullable=True)
    conversion_probability = Column(Float, nullable=True)  # Predicted probability
    expected_conversions = Column(Float, nullable=True)  # Predicted count
    
    # Statistical confidence
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    confidence_interval_low = Column(Float, nullable=True)  # Lower bound of ROAS CI
    confidence_interval_high = Column(Float, nullable=True)  # Upper bound of ROAS CI
    sample_size = Column(Integer, nullable=True)  # Number of data points
    
    # Bayesian smoothing
    prior_roas = Column(Float, nullable=True)  # Prior belief
    posterior_roas = Column(Float, nullable=True)  # Posterior after Bayesian update
    smoothing_factor = Column(Float, nullable=True)  # Weight of prior
    
    # Performance indicators
    is_outlier = Column(Integer, nullable=False, default=0)  # 1 if statistical outlier
    outlier_reason = Column(String(255), nullable=True)  # Explanation
    performance_tier = Column(String(50), nullable=True)  # excellent, good, average, poor, failing
    
    # Optimization recommendations
    recommendation = Column(String(50), nullable=True)  # scale_up, scale_down, pause, monitor, test
    recommended_budget_change_pct = Column(Float, nullable=True)  # -100 to +200 (percentage change)
    recommended_daily_budget_usd = Column(Float, nullable=True)  # New recommended budget
    
    # Quality scores
    session_quality_score = Column(Float, nullable=True)  # 0.0 to 100.0
    user_retention_probability = Column(Float, nullable=True)  # 0.0 to 1.0
    lifetime_value_estimate = Column(Float, nullable=True)  # Predicted LTV
    
    # Blended metrics (insights + outcomes)
    blended_ctr = Column(Float, nullable=True)
    blended_cpc = Column(Float, nullable=True)
    blended_cpm = Column(Float, nullable=True)
    
    # Metadata
    calculation_method = Column(String(100), nullable=True)  # bayesian, frequentist, ml_model, etc.
    model_version = Column(String(50), nullable=True)  # Version of prediction model used
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ad = relationship("MetaAdModel", foreign_keys=[ad_id])
    adset = relationship("MetaAdsetModel", foreign_keys=[adset_id])
    campaign = relationship("MetaCampaignModel", foreign_keys=[campaign_id])
    
    # Unique constraint: one record per ad/adset/campaign per date
    __table_args__ = (
        UniqueConstraint('ad_id', 'date', name='uix_roas_ad_date'),
        UniqueConstraint('adset_id', 'date', name='uix_roas_adset_date'),
        UniqueConstraint('campaign_id', 'date', name='uix_roas_campaign_date'),
    )
    
    def __repr__(self):
        return f"<MetaROASMetrics(id={self.id}, actual_roas={self.actual_roas}, predicted_roas={self.predicted_roas})>"
