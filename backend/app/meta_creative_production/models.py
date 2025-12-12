"""SQLAlchemy models for Meta Creative Production Engine (PASO 10.17)"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.core.database import Base

class MetaCreativeProductionModel(Base):
    """Master creative with human inputs (PASO 10.17)"""
    __tablename__ = "meta_creative_productions"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Master creative
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Human inputs (cannot be changed by system)
    authorized_pixels = Column(JSONB, nullable=False)  # List[str]
    authorized_subgenres = Column(JSONB, nullable=False)  # List[str]
    genre = Column(String(100), nullable=False, index=True)
    
    # Fragments and style
    fragments = Column(JSONB, nullable=False)  # List[CreativeFragmentInput]
    style_guide = Column(JSONB, nullable=False)  # StyleGuideInput
    human_instructions = Column(Text, nullable=True)
    
    # Metadata
    campaign_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    total_variants_generated = Column(Integer, default=0, nullable=False)
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_meta_productions_active_mode', 'is_active', 'mode'),
        Index('ix_meta_productions_campaign_genre', 'campaign_id', 'genre'),
    )

class MetaCreativeVariantModel(Base):
    """Generated creative variant (PASO 10.17)"""
    __tablename__ = "meta_creative_variants"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Parent relationship
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey('meta_creative_productions.id'), 
                      nullable=False, index=True)
    variant_number = Column(Integer, nullable=False)  # 1-15
    
    # Variant details
    variant_type = Column(String(50), nullable=False, index=True)  # VariantType enum
    narrative_structure = Column(String(50), nullable=False, index=True)  # NarrativeStructure
    
    # Content
    fragments_order = Column(JSONB, nullable=False)  # List[UUID] - fragment IDs
    caption = Column(Text, nullable=False)
    hashtags = Column(JSONB, nullable=False)  # List[str]
    text_overlay = Column(String(500), nullable=True)
    
    # Technical
    duration_seconds = Column(Float, nullable=False)
    duration_category = Column(String(20), nullable=False, index=True)  # short/medium/long
    color_lut = Column(String(100), nullable=True)
    
    # Changes from parent
    changes = Column(JSONB, nullable=False)  # Dict of changes made
    
    # Performance & scores
    estimated_score = Column(Float, nullable=False, index=True)  # 0-100
    confidence = Column(Float, nullable=False)  # 0-1
    actual_performance = Column(JSONB, nullable=True)  # Real metrics from 10.15
    performance_score = Column(Float, nullable=True, index=True)  # Real score
    
    # Meta Ads integration
    meta_creative_id = Column(String(100), nullable=True, index=True)
    meta_ad_id = Column(String(100), nullable=True, index=True)
    upload_status = Column(String(20), nullable=False, default="generated", index=True)
    uploaded_at = Column(DateTime, nullable=True)
    
    # Campaign association
    campaign_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    adset_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    
    # Lifecycle
    status = Column(String(20), default="generated", nullable=False, index=True)
    days_active = Column(Integer, default=0, nullable=False)
    is_fatigued = Column(Boolean, default=False, nullable=False, index=True)
    fatigue_score = Column(Float, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_variants_parent_status', 'parent_id', 'status'),
        Index('ix_variants_campaign_performance', 'campaign_id', 'performance_score'),
        Index('ix_variants_fatigue_status', 'is_fatigued', 'status'),
        Index('ix_variants_duration_category', 'duration_category', 'estimated_score'),
        Index('ix_variants_narrative_structure', 'narrative_structure', 'status'),
    )

class MetaCreativeFragmentModel(Base):
    """Approved fragment with performance tracking (PASO 10.17)"""
    __tablename__ = "meta_creative_fragments"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Fragment details
    fragment_type = Column(String(20), nullable=False, index=True)  # hook/body/cta/outro
    video_url = Column(String(500), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    # Master creative relationship
    master_creative_id = Column(PGUUID(as_uuid=True), 
                                ForeignKey('meta_creative_productions.id'),
                                nullable=True, index=True)
    
    # Approval
    approved = Column(Boolean, default=False, nullable=False, index=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Performance tracking
    performance_score = Column(Float, nullable=True, index=True)  # 0-100
    usage_count = Column(Integer, default=0, nullable=False)  # Times used in variants
    success_rate = Column(Float, nullable=True)  # % of successful variants
    
    # Best use cases
    best_for_structure = Column(String(50), nullable=True, index=True)  # Best narrative structure
    best_with_pixels = Column(JSONB, nullable=True)  # List[str] pixels where it performs best
    performance_by_structure = Column(JSONB, nullable=True)  # Dict[structure, score]
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_used = Column(DateTime, nullable=True)
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_fragments_type_score', 'fragment_type', 'performance_score'),
        Index('ix_fragments_approved_usage', 'approved', 'usage_count'),
        Index('ix_fragments_master_type', 'master_creative_id', 'fragment_type'),
    )

class MetaCreativePromotionLogModel(Base):
    """Upload and promotion tracking (PASO 10.17)"""
    __tablename__ = "meta_creative_promotion_logs"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Variant relationship
    variant_id = Column(PGUUID(as_uuid=True), ForeignKey('meta_creative_variants.id'),
                       nullable=False, index=True)
    
    # Promotion details
    promotion_type = Column(String(20), nullable=False, index=True)  # test/scale/winner
    
    # Meta Ads IDs
    meta_creative_id = Column(String(100), nullable=True, index=True)
    meta_ad_id = Column(String(100), nullable=True, index=True)
    meta_campaign_id = Column(String(100), nullable=True)
    meta_adset_id = Column(String(100), nullable=True)
    
    # Local associations
    campaign_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    adset_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Promotion status
    promotion_status = Column(String(20), default="pending", nullable=False, index=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_timestamp = Column(DateTime, nullable=True)
    
    # Results
    success = Column(Boolean, default=False, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Budget & targeting
    budget_allocated = Column(Float, nullable=True)
    targeting_details = Column(JSONB, nullable=True)
    
    # Metadata
    promoted_by = Column(String(100), nullable=True)  # scheduler/manual/api
    mode = Column(String(20), default="stub", nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_promotion_variant_status', 'variant_id', 'promotion_status'),
        Index('ix_promotion_campaign_success', 'campaign_id', 'success'),
        Index('ix_promotion_type_timestamp', 'promotion_type', 'upload_timestamp'),
    )
