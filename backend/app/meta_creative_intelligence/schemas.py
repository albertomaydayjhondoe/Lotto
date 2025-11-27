"""
Pydantic schemas para Meta Creative Intelligence System
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1. VISUAL ANALYSIS SCHEMAS
# ============================================================================

class ObjectDetection(BaseModel):
    """Objeto detectado en el video"""
    model_config = ConfigDict(from_attributes=True)
    
    label: str = Field(..., description="Etiqueta del objeto (person, car, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de detección")
    bbox: list[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    frame_number: int = Field(..., description="Frame donde aparece")


class FaceDetection(BaseModel):
    """Rostro detectado"""
    model_config = ConfigDict(from_attributes=True)
    
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: list[float]
    frame_number: int
    emotion: Optional[str] = None  # "happy", "neutral", "sad", etc.
    age_range: Optional[str] = None  # "18-25", "26-35", etc.
    gender: Optional[str] = None  # "male", "female", "unknown"


class TextDetection(BaseModel):
    """Texto detectado (OCR)"""
    model_config = ConfigDict(from_attributes=True)
    
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: list[float]
    frame_number: int
    language: Optional[str] = None


class VisualScoring(BaseModel):
    """Scoring visual del video"""
    model_config = ConfigDict(from_attributes=True)
    
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Score global 0-100")
    face_score: float = Field(..., ge=0.0, le=100.0, description="Presencia de rostros")
    action_score: float = Field(..., ge=0.0, le=100.0, description="Nivel de acción/movimiento")
    text_score: float = Field(..., ge=0.0, le=100.0, description="Presencia de texto")
    color_score: float = Field(..., ge=0.0, le=100.0, description="Vibrancia de colores")
    composition_score: float = Field(..., ge=0.0, le=100.0, description="Composición visual")
    engagement_potential: float = Field(..., ge=0.0, le=100.0, description="Potencial de engagement")


class FragmentExtraction(BaseModel):
    """Fragmento extraído con alto potencial"""
    model_config = ConfigDict(from_attributes=True)
    
    start_frame: int
    end_frame: int
    duration_seconds: float
    score: float = Field(..., ge=0.0, le=100.0)
    reason: str = Field(..., description="Razón de la extracción")
    features: dict[str, Any] = Field(default_factory=dict)


class VisualAnalysisRequest(BaseModel):
    """Request para análisis visual"""
    model_config = ConfigDict(from_attributes=True)
    
    video_asset_id: UUID
    mode: str = Field(default="stub", pattern="^(stub|live)$")
    detect_objects: bool = True
    detect_faces: bool = True
    detect_text: bool = True
    extract_fragments: bool = True
    max_fragments: int = Field(default=5, ge=1, le=20)


class VisualAnalysisResponse(BaseModel):
    """Response del análisis visual"""
    model_config = ConfigDict(from_attributes=True)
    
    analysis_id: UUID
    video_asset_id: UUID
    mode: str
    objects: list[ObjectDetection]
    faces: list[FaceDetection]
    texts: list[TextDetection]
    scoring: VisualScoring
    fragments: list[FragmentExtraction]
    processing_time_ms: float
    created_at: datetime


# ============================================================================
# 2. VARIANT GENERATION SCHEMAS
# ============================================================================

class VariantConfig(BaseModel):
    """Configuración para generar variantes"""
    model_config = ConfigDict(from_attributes=True)
    
    reorder_fragments: bool = True
    add_subtitles: bool = True
    add_overlays: bool = True
    vary_music: bool = False  # STUB mode
    vary_duration: bool = True
    min_variants: int = Field(default=5, ge=1, le=20)
    max_variants: int = Field(default=10, ge=1, le=20)


class VariantMetadata(BaseModel):
    """Metadata de una variante generada"""
    model_config = ConfigDict(from_attributes=True)
    
    variant_number: int
    changes: dict[str, Any] = Field(default_factory=dict, description="Cambios aplicados")
    duration_seconds: float
    estimated_score: float = Field(..., ge=0.0, le=100.0)
    asset_url: Optional[str] = None


class VariantGenerationRequest(BaseModel):
    """Request para generar variantes"""
    model_config = ConfigDict(from_attributes=True)
    
    video_asset_id: UUID
    analysis_id: Optional[UUID] = None  # Si existe análisis previo
    config: VariantConfig = Field(default_factory=VariantConfig)
    mode: str = Field(default="stub", pattern="^(stub|live)$")


class VariantGenerationResponse(BaseModel):
    """Response de generación de variantes"""
    model_config = ConfigDict(from_attributes=True)
    
    generation_id: UUID
    video_asset_id: UUID
    variants: list[VariantMetadata]
    total_variants: int
    processing_time_ms: float
    created_at: datetime


# ============================================================================
# 3. WINNER SELECTION SCHEMAS
# ============================================================================

class PerformanceMetrics(BaseModel):
    """Métricas de performance de un creative"""
    model_config = ConfigDict(from_attributes=True)
    
    roas: Optional[float] = None
    ctr: Optional[float] = None  # Click-Through Rate
    cvr: Optional[float] = None  # Conversion Rate
    view_depth: Optional[float] = None  # % de video visto
    engagement_rate: Optional[float] = None
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0


class WinnerSelectionRequest(BaseModel):
    """Request para seleccionar ganador"""
    model_config = ConfigDict(from_attributes=True)
    
    campaign_id: UUID
    candidate_asset_ids: list[UUID] = Field(..., min_length=2)
    criteria_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "roas": 0.40,
            "ctr": 0.25,
            "cvr": 0.20,
            "view_depth": 0.15,
        }
    )
    min_impressions: int = Field(default=1000, description="Mínimo de impresiones para considerar")


class WinnerSelectionResponse(BaseModel):
    """Response de selección de ganador"""
    model_config = ConfigDict(from_attributes=True)
    
    selection_id: UUID
    campaign_id: UUID
    winner_asset_id: UUID
    winner_score: float = Field(..., ge=0.0, le=100.0)
    runner_up_asset_id: Optional[UUID] = None
    runner_up_score: Optional[float] = None
    all_scores: dict[str, float] = Field(default_factory=dict)
    reasoning: str
    performance_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# ============================================================================
# 4. THUMBNAIL GENERATION SCHEMAS
# ============================================================================

class ThumbnailCandidate(BaseModel):
    """Candidato a thumbnail"""
    model_config = ConfigDict(from_attributes=True)
    
    frame_number: int
    timestamp_seconds: float
    score: float = Field(..., ge=0.0, le=100.0)
    features: dict[str, Any] = Field(default_factory=dict)
    has_face: bool = False
    has_action: bool = False
    has_text: bool = False


class ThumbnailGenerationRequest(BaseModel):
    """Request para generar thumbnail"""
    model_config = ConfigDict(from_attributes=True)
    
    video_asset_id: UUID
    analysis_id: Optional[UUID] = None
    max_candidates: int = Field(default=5, ge=1, le=10)
    prefer_faces: bool = True
    prefer_action: bool = True
    avoid_text: bool = False
    mode: str = Field(default="stub", pattern="^(stub|live)$")


class ThumbnailGenerationResponse(BaseModel):
    """Response de generación de thumbnail"""
    model_config = ConfigDict(from_attributes=True)
    
    thumbnail_id: UUID
    video_asset_id: UUID
    selected_frame: int
    selected_timestamp: float
    thumbnail_url: Optional[str] = None
    candidates: list[ThumbnailCandidate]
    reasoning: str
    created_at: datetime


# ============================================================================
# 5. LIFECYCLE MANAGEMENT SCHEMAS
# ============================================================================

class FatigueDetectionResult(BaseModel):
    """Resultado de detección de fatiga"""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    is_fatigued: bool
    fatigue_score: float = Field(..., ge=0.0, le=100.0, description="0=fresco, 100=muy fatigado")
    metrics_trend: dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    days_active: int
    impressions_total: int


class RenewalRequest(BaseModel):
    """Request para renovar creative"""
    model_config = ConfigDict(from_attributes=True)
    
    creative_id: UUID
    strategy: str = Field(
        default="generate_variant",
        description="generate_variant, replace_entirely, refresh_targeting"
    )
    auto_apply: bool = False


class RenewalResponse(BaseModel):
    """Response de renovación"""
    model_config = ConfigDict(from_attributes=True)
    
    renewal_id: UUID
    creative_id: UUID
    strategy: str
    new_creative_id: Optional[UUID] = None
    actions_taken: list[str]
    success: bool
    message: str
    created_at: datetime


class LifecycleHistoryResponse(BaseModel):
    """Historial del lifecycle"""
    model_config = ConfigDict(from_attributes=True)
    
    lifecycle_id: UUID
    creative_id: UUID
    action: str
    details: dict[str, Any] = Field(default_factory=dict)
    success: bool
    created_at: datetime


# ============================================================================
# 6. ORCHESTRATOR SCHEMAS
# ============================================================================

class CreativeIntelligenceRunRequest(BaseModel):
    """Request para ejecutar el orchestrator completo"""
    model_config = ConfigDict(from_attributes=True)
    
    video_asset_ids: list[UUID] = Field(..., min_length=1)
    enable_analysis: bool = True
    enable_variants: bool = True
    enable_thumbnails: bool = True
    enable_lifecycle_check: bool = True
    mode: str = Field(default="stub", pattern="^(stub|live)$")


class CreativeIntelligenceRunResponse(BaseModel):
    """Response del orchestrator"""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: UUID
    video_assets_processed: int
    analyses_completed: int
    variants_generated: int
    thumbnails_created: int
    fatigues_detected: int
    duration_ms: float
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# ============================================================================
# 7. GENERIC RESPONSES
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    subsystems: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
