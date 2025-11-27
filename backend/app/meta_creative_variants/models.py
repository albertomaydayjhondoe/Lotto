"""
SQLAlchemy models para Meta Creative Variants Engine (PASO 10.10)
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


# ==================== Enums ====================


class VariantStatusEnum(str, enum.Enum):
    """Estado de una variante creativa."""
    DRAFT = "draft"
    GENERATED = "generated"
    UPLOADED = "uploaded"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    FAILED = "failed"


# ==================== Models ====================


class MetaCreativeVariantModel(Base):
    """
    Variante creativa completa (combinación de video + texto + thumbnail).
    Representa un anuncio único en Meta Ads.
    """
    __tablename__ = "meta_creative_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(String(128), unique=True, nullable=False, index=True)
    
    # Relaciones con Meta Ads
    campaign_id = Column(String(128), nullable=True, index=True)
    adset_id = Column(String(128), nullable=True, index=True)
    
    # Relaciones con componentes
    video_variant_id = Column(Integer, ForeignKey("meta_creative_variant_videos.id"), nullable=False)
    text_variant_id = Column(Integer, ForeignKey("meta_creative_variant_texts.id"), nullable=False)
    thumbnail_variant_id = Column(Integer, ForeignKey("meta_creative_variant_thumbnails.id"), nullable=False)
    
    # Estado y Meta API
    status = Column(SQLEnum(VariantStatusEnum), default=VariantStatusEnum.DRAFT, nullable=False, index=True)
    meta_creative_id = Column(String(128), nullable=True, unique=True, index=True)
    meta_ad_id = Column(String(128), nullable=True, unique=True, index=True)
    
    # Performance metrics (actualizados desde Insights)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    
    # Metadata
    generated_by = Column(String(50), default="auto")  # auto, manual, ai
    generation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    video_variant = relationship("MetaCreativeVariantVideoModel", back_populates="creative_variant", foreign_keys=[video_variant_id])
    text_variant = relationship("MetaCreativeVariantTextModel", back_populates="creative_variant", foreign_keys=[text_variant_id])
    thumbnail_variant = relationship("MetaCreativeVariantThumbnailModel", back_populates="creative_variant", foreign_keys=[thumbnail_variant_id])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MetaCreativeVariantVideoModel(Base):
    """
    Variante de video con parámetros de edición.
    """
    __tablename__ = "meta_creative_variant_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(String(128), unique=True, nullable=False, index=True)
    clip_id = Column(String(128), nullable=False, index=True)
    
    # Fragmento temporal
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    # Parámetros de edición
    crop_ratio = Column(String(10), nullable=False, default="1:1")  # 1:1, 9:16, 4:5, 16:9
    speed = Column(String(10), nullable=False, default="1.0x")  # 0.9x, 1.0x, 1.1x
    muted = Column(Boolean, default=False, nullable=False)
    subtitles_enabled = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    scene_description = Column(Text, nullable=True)
    thumbnail_timestamp = Column(Float, nullable=True)
    file_url = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Relationships
    creative_variant = relationship("MetaCreativeVariantModel", back_populates="video_variant", foreign_keys="MetaCreativeVariantModel.video_variant_id")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MetaCreativeVariantTextModel(Base):
    """
    Variante de textos para el anuncio.
    """
    __tablename__ = "meta_creative_variant_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(String(128), unique=True, nullable=False, index=True)
    
    # Textos principales
    headline = Column(String(40), nullable=False)
    primary_text = Column(String(125), nullable=False)
    description = Column(String(30), nullable=True)
    
    # CTA
    cta_type = Column(String(50), nullable=False, default="learn_more")
    cta_text = Column(String(25), nullable=True)
    
    # Metadata
    language = Column(String(5), nullable=False, default="es")
    keywords = Column(JSON, nullable=True)  # Lista de keywords
    hashtags = Column(JSON, nullable=True)  # Lista de hashtags
    
    # Relationships
    creative_variant = relationship("MetaCreativeVariantModel", back_populates="text_variant", foreign_keys="MetaCreativeVariantModel.text_variant_id")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MetaCreativeVariantThumbnailModel(Base):
    """
    Variante de thumbnail.
    """
    __tablename__ = "meta_creative_variant_thumbnails"
    
    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(String(128), unique=True, nullable=False, index=True)
    
    # Source
    source_type = Column(String(50), nullable=False)  # freeze_frame, extract_frame, overlay
    timestamp = Column(Float, nullable=True)  # Timestamp del frame si aplica
    
    # Edición
    has_text_overlay = Column(Boolean, default=False, nullable=False)
    overlay_text = Column(String(50), nullable=True)
    crop_ratio = Column(String(10), nullable=False, default="1:1")
    
    # Output
    file_url = Column(String(512), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Relationships
    creative_variant = relationship("MetaCreativeVariantModel", back_populates="thumbnail_variant", foreign_keys="MetaCreativeVariantModel.thumbnail_variant_id")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
