"""
Database models para Meta Creative Intelligence System
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MetaCreativeAnalysisModel(Base):
    """
    Análisis visual completo de un creative/video.
    Almacena detecciones de objetos, rostros, texto, scoring y fragmentos extraídos.
    """
    __tablename__ = "meta_creative_analysis"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    video_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Mode
    mode = Column(String(20), nullable=False, default="stub")  # "stub" | "live"
    
    # Detection Results (JSON)
    objects_detected = Column(JSON, nullable=True, default=list)  # [ObjectDetection]
    faces_detected = Column(JSON, nullable=True, default=list)  # [FaceDetection]
    texts_detected = Column(JSON, nullable=True, default=list)  # [TextDetection]
    
    # Scoring (JSON)
    visual_scoring = Column(JSON, nullable=True, default=dict)  # VisualScoring
    
    # Fragments (JSON)
    fragments_extracted = Column(JSON, nullable=True, default=list)  # [FragmentExtraction]
    
    # Metrics
    total_objects = Column(Integer, default=0)
    total_faces = Column(Integer, default=0)
    total_texts = Column(Integer, default=0)
    total_fragments = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)  # Cached from visual_scoring
    
    # Processing
    processing_time_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_creative_analysis_video_created', 'video_asset_id', 'created_at'),
        Index('idx_creative_analysis_score', 'overall_score'),
        Index('idx_creative_analysis_mode', 'mode'),
    )


class MetaCreativeVariantGenerationModel(Base):
    """
    Generación de variantes de un creative base.
    Almacena configuración y metadata de todas las variantes generadas.
    """
    __tablename__ = "meta_creative_variant_generation"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    video_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('meta_creative_analysis.id'), nullable=True, index=True)
    
    # Mode
    mode = Column(String(20), nullable=False, default="stub")
    
    # Configuration (JSON)
    config = Column(JSON, nullable=False, default=dict)  # VariantConfig
    
    # Generated Variants (JSON Array)
    variants = Column(JSON, nullable=False, default=list)  # [VariantMetadata]
    
    # Metrics
    total_variants = Column(Integer, default=0)
    variants_with_reorder = Column(Integer, default=0)
    variants_with_subtitles = Column(Integer, default=0)
    variants_with_overlays = Column(Integer, default=0)
    variants_with_music_change = Column(Integer, default=0)
    
    # Processing
    processing_time_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("MetaCreativeAnalysisModel", foreign_keys=[analysis_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_variant_gen_video_created', 'video_asset_id', 'created_at'),
        Index('idx_variant_gen_analysis', 'analysis_id'),
    )


class MetaPublicationWinnerModel(Base):
    """
    Selección del creative ganador para publicación.
    Basado en performance real: ROAS, CTR, CVR, ViewDepth.
    """
    __tablename__ = "meta_publication_winner"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    campaign_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    winner_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    runner_up_asset_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Selection Criteria
    criteria_weights = Column(JSON, nullable=False, default=dict)  # {"roas": 0.4, ...}
    min_impressions = Column(Integer, default=1000)
    
    # Scores
    winner_score = Column(Float, nullable=False)
    runner_up_score = Column(Float, nullable=True)
    all_scores = Column(JSON, nullable=True, default=dict)  # {asset_id: score}
    
    # Performance Summary (JSON)
    performance_summary = Column(JSON, nullable=True, default=dict)
    
    # Reasoning
    reasoning = Column(Text, nullable=True)
    
    # Status
    published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_winner_campaign_created', 'campaign_id', 'created_at'),
        Index('idx_winner_asset', 'winner_asset_id'),
        Index('idx_winner_published', 'published', 'published_at'),
    )


class MetaThumbnailModel(Base):
    """
    Thumbnail generado automáticamente para un video.
    Almacena frame seleccionado y candidatos evaluados.
    """
    __tablename__ = "meta_thumbnail"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    video_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('meta_creative_analysis.id'), nullable=True, index=True)
    
    # Mode
    mode = Column(String(20), nullable=False, default="stub")
    
    # Selected Thumbnail
    selected_frame = Column(Integer, nullable=False)
    selected_timestamp = Column(Float, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    
    # Candidates Evaluated (JSON)
    candidates = Column(JSON, nullable=False, default=list)  # [ThumbnailCandidate]
    
    # Selection Config
    prefer_faces = Column(Boolean, default=True)
    prefer_action = Column(Boolean, default=True)
    avoid_text = Column(Boolean, default=False)
    
    # Reasoning
    reasoning = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("MetaCreativeAnalysisModel", foreign_keys=[analysis_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_thumbnail_video_created', 'video_asset_id', 'created_at'),
        Index('idx_thumbnail_analysis', 'analysis_id'),
    )


class MetaCreativeLifecycleModel(Base):
    """
    Gestión del ciclo de vida de creatives.
    Detecta fatiga y registra acciones de renovación.
    """
    __tablename__ = "meta_creative_lifecycle"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    creative_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # MetaCreativeModel o video_asset_id
    
    # Action Type
    action = Column(String(50), nullable=False, index=True)  # "fatigue_detection", "renewal", "refresh"
    strategy = Column(String(50), nullable=True)  # "generate_variant", "replace_entirely", etc.
    
    # Fatigue Detection
    is_fatigued = Column(Boolean, nullable=True)
    fatigue_score = Column(Float, nullable=True)  # 0-100
    
    # Metrics Snapshot (JSON)
    metrics_trend = Column(JSON, nullable=True, default=dict)
    
    # Renewal
    new_creative_id = Column(UUID(as_uuid=True), nullable=True)
    actions_taken = Column(JSON, nullable=True, default=list)
    
    # Lifecycle Metrics
    days_active = Column(Integer, nullable=True)
    impressions_total = Column(Integer, nullable=True)
    
    # Result
    success = Column(Boolean, default=True)
    recommendation = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    
    # Details (JSON)
    details = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_lifecycle_creative_action', 'creative_id', 'action'),
        Index('idx_lifecycle_fatigued', 'is_fatigued', 'fatigue_score'),
        Index('idx_lifecycle_created', 'created_at'),
    )
