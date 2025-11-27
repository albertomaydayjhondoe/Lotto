"""
Pydantic schemas para Meta Creative Variants Engine (PASO 10.10)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==================== Enums ====================


class VariantStatus(str, Enum):
    """Estado de una variante creativa."""
    DRAFT = "draft"
    GENERATED = "generated"
    UPLOADED = "uploaded"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    FAILED = "failed"


class CropRatio(str, Enum):
    """Aspect ratios para crops de video."""
    SQUARE = "1:1"  # Instagram Feed
    VERTICAL = "9:16"  # Instagram Stories, Reels
    PORTRAIT = "4:5"  # Instagram Feed vertical
    HORIZONTAL = "16:9"  # YouTube, Facebook
    WIDE = "2:1"  # Banners


class VideoSpeed(str, Enum):
    """Velocidades de reproducción."""
    SLOW = "0.9x"
    NORMAL = "1.0x"
    FAST = "1.1x"


class CTAType(str, Enum):
    """Tipos de Call-to-Action."""
    LEARN_MORE = "learn_more"
    SHOP_NOW = "shop_now"
    SIGN_UP = "sign_up"
    DOWNLOAD = "download"
    WATCH_MORE = "watch_more"
    GET_OFFER = "get_offer"
    APPLY_NOW = "apply_now"
    BOOK_NOW = "book_now"


# ==================== Video Variant Schemas ====================


class VideoVariant(BaseModel):
    """Variante de video con parámetros de edición."""
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: str = Field(description="ID único de la variante")
    clip_id: str = Field(description="ID del clip base")
    
    # Fragmento temporal
    start_time: float = Field(ge=0, description="Tiempo de inicio en segundos")
    end_time: float = Field(ge=0, description="Tiempo de fin en segundos")
    duration: float = Field(ge=0, description="Duración total en segundos")
    
    # Parámetros de edición
    crop_ratio: CropRatio = Field(default=CropRatio.SQUARE)
    speed: VideoSpeed = Field(default=VideoSpeed.NORMAL)
    muted: bool = Field(default=False, description="Si el video está silenciado")
    subtitles_enabled: bool = Field(default=True, description="Si mostrar subtítulos")
    
    # Metadata
    scene_description: Optional[str] = None
    thumbnail_timestamp: Optional[float] = None
    file_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Text Variant Schemas ====================


class TextVariant(BaseModel):
    """Variante de textos para el anuncio."""
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: str = Field(description="ID único de la variante")
    
    # Textos principales
    headline: str = Field(max_length=40, description="Título del anuncio (max 40 chars)")
    primary_text: str = Field(max_length=125, description="Texto principal (max 125 chars)")
    description: Optional[str] = Field(max_length=30, default=None, description="Descripción (max 30 chars)")
    
    # CTA
    cta_type: CTAType = Field(default=CTAType.LEARN_MORE)
    cta_text: Optional[str] = Field(max_length=25, default=None)
    
    # Metadata
    language: str = Field(default="es", description="Idioma del texto")
    keywords: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Thumbnail Variant Schemas ====================


class ThumbnailVariant(BaseModel):
    """Variante de thumbnail."""
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: str = Field(description="ID único de la variante")
    
    # Source
    source_type: str = Field(description="freeze_frame, extract_frame, overlay")
    timestamp: Optional[float] = Field(default=None, description="Timestamp del frame (segundos)")
    
    # Edición
    has_text_overlay: bool = Field(default=False)
    overlay_text: Optional[str] = Field(max_length=50, default=None)
    crop_ratio: CropRatio = Field(default=CropRatio.SQUARE)
    
    # Output
    file_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Creative Variant (Combinación) ====================


class CreativeVariant(BaseModel):
    """
    Variante creativa completa: combinación de video + texto + thumbnail.
    Representa un anuncio único listo para subir a Meta Ads.
    """
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: str = Field(description="ID único de la variante completa")
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    
    # Componentes
    video_variant: VideoVariant
    text_variant: TextVariant
    thumbnail_variant: ThumbnailVariant
    
    # Estado y Meta API
    status: VariantStatus = Field(default=VariantStatus.DRAFT)
    meta_creative_id: Optional[str] = Field(default=None, description="ID del creative en Meta Ads")
    meta_ad_id: Optional[str] = Field(default=None, description="ID del ad en Meta Ads")
    
    # Performance (si ya está activo)
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    spend: float = Field(default=0.0)
    ctr: float = Field(default=0.0)
    
    # Metadata
    generated_by: str = Field(default="auto", description="auto, manual, ai")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    uploaded_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None


# ==================== Request/Response Schemas ====================


class GenerateVariantsRequest(BaseModel):
    """Request para generar variantes creativas."""
    clip_id: str = Field(description="ID del clip base para generar variantes")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID de Meta Ads")
    adset_id: Optional[str] = Field(default=None, description="Adset ID de Meta Ads")
    
    # Parámetros de generación
    num_variants: int = Field(default=10, ge=5, le=20, description="Número de variantes a generar (5-20)")
    video_variants_count: int = Field(default=5, ge=3, le=7, description="Variantes de video (3-7)")
    text_variants_count: int = Field(default=5, ge=3, le=10, description="Variantes de texto (3-10)")
    thumbnail_variants_count: int = Field(default=4, ge=3, le=6, description="Variantes de thumbnail (3-6)")
    
    # Filtros
    crop_ratios: List[CropRatio] = Field(default_factory=lambda: [CropRatio.SQUARE, CropRatio.VERTICAL])
    languages: List[str] = Field(default_factory=lambda: ["es"])
    cta_types: List[CTAType] = Field(default_factory=lambda: [CTAType.LEARN_MORE, CTAType.SHOP_NOW])
    
    # Opciones
    auto_upload: bool = Field(default=False, description="Si subir automáticamente a Meta Ads")
    dry_run: bool = Field(default=False, description="Si solo simular sin crear nada")


class GenerateVariantsResponse(BaseModel):
    """Response de generación de variantes."""
    success: bool
    clip_id: str
    campaign_id: Optional[str] = None
    
    # Resultados
    total_variants: int
    variants: List[CreativeVariant]
    
    # Estadísticas
    video_variants_generated: int
    text_variants_generated: int
    thumbnail_variants_generated: int
    
    # Upload (si auto_upload=True)
    uploaded_count: int = Field(default=0)
    upload_errors: List[str] = Field(default_factory=list)
    
    # Metadata
    generation_time_seconds: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class UploadVariantRequest(BaseModel):
    """Request para subir una variante a Meta Ads."""
    variant_id: str
    campaign_id: str
    adset_id: str
    ad_account_id: str


class UploadVariantResponse(BaseModel):
    """Response de upload de variante."""
    success: bool
    variant_id: str
    meta_creative_id: Optional[str] = None
    meta_ad_id: Optional[str] = None
    error: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class BulkUploadRequest(BaseModel):
    """Request para upload masivo de variantes."""
    campaign_id: str
    adset_id: str
    ad_account_id: str
    variant_ids: List[str] = Field(description="Lista de variant_ids a subir")
    max_parallel: int = Field(default=3, ge=1, le=5, description="Máximo de uploads paralelos")


class BulkUploadResponse(BaseModel):
    """Response de upload masivo."""
    success: bool
    campaign_id: str
    total_requested: int
    uploaded_count: int
    failed_count: int
    
    results: List[UploadVariantResponse]
    errors: List[str] = Field(default_factory=list)
    
    upload_time_seconds: float
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class ListVariantsResponse(BaseModel):
    """Response de listado de variantes."""
    total: int
    variants: List[CreativeVariant]
    campaign_id: Optional[str] = None
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class RegenerateVariantRequest(BaseModel):
    """Request para regenerar una variante específica."""
    variant_id: str
    regenerate_video: bool = Field(default=False)
    regenerate_text: bool = Field(default=False)
    regenerate_thumbnail: bool = Field(default=False)
    
    # Nuevos parámetros (si se especifican)
    new_crop_ratio: Optional[CropRatio] = None
    new_cta_type: Optional[CTAType] = None
