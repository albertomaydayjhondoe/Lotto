"""
Content Engine - Pydantic Models
Modelos de datos con validación estricta.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ContentAnalysisRequest(BaseModel):
    """Request para análisis de contenido."""
    
    video_id: str = Field(..., description="ID único del video")
    video_url: Optional[str] = Field(None, description="URL del video")
    video_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata adicional del video"
    )
    target_platform: str = Field(
        default="instagram",
        description="Plataforma objetivo (instagram, tiktok, youtube)"
    )
    generate_hooks: bool = Field(default=True)
    generate_captions: bool = Field(default=True)
    analyze_trends: bool = Field(default=True)
    
    @validator("target_platform")
    def validate_platform(cls, v):
        allowed = ["instagram", "tiktok", "youtube", "facebook"]
        if v.lower() not in allowed:
            raise ValueError(f"Platform must be one of {allowed}")
        return v.lower()


class VideoAnalysisResult(BaseModel):
    """Resultado del análisis técnico de video."""
    
    video_id: str
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    format: Optional[str] = None
    file_size_mb: Optional[float] = None
    has_audio: bool = True
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calidad técnica (0-1)"
    )
    technical_issues: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class TrendAnalysisResult(BaseModel):
    """Resultado del análisis de tendencias."""
    
    video_id: str
    detected_trends: List[str] = Field(default_factory=list)
    trending_hashtags: List[str] = Field(default_factory=list)
    trending_sounds: List[str] = Field(default_factory=list)
    viral_potential: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Potencial viral (0-1)"
    )
    trend_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedHook(BaseModel):
    """Hook generado por LLM."""
    
    text: str = Field(..., min_length=10, max_length=500)
    type: str = Field(
        default="question",
        description="Tipo de hook (question, statement, challenge, etc.)"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    target_emotion: Optional[str] = None
    estimated_engagement: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class GeneratedCaption(BaseModel):
    """Caption generado por LLM."""
    
    text: str = Field(..., min_length=20, max_length=2200)
    hashtags: List[str] = Field(default_factory=list)
    emojis: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    character_count: int = Field(default=0)
    
    @validator("character_count", always=True)
    def calculate_character_count(cls, v, values):
        if "text" in values:
            return len(values["text"])
        return v


class GeneratedContent(BaseModel):
    """Contenido generado completo."""
    
    video_id: str
    hooks: List[GeneratedHook] = Field(default_factory=list)
    captions: List[GeneratedCaption] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    prompt_version: str = Field(default="1.0.0")
    model_used: str = Field(default="gpt-4o-mini")
    total_tokens: int = Field(default=0)
    estimated_cost_eur: float = Field(default=0.0)


class ContentMetrics(BaseModel):
    """Métricas de telemetría."""
    
    request_id: str
    video_id: str
    execution_time_ms: float
    tokens_used: int
    cost_eur: float
    model_used: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContentAnalysisResponse(BaseModel):
    """Response completo del análisis de contenido."""
    
    video_id: str
    request_id: str = Field(default_factory=lambda: f"req_{datetime.utcnow().timestamp()}")
    
    # Results
    video_analysis: Optional[VideoAnalysisResult] = None
    trend_analysis: Optional[TrendAnalysisResult] = None
    generated_content: Optional[GeneratedContent] = None
    
    # Metadata
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    total_cost_eur: float = 0.0
    
    # Metrics
    metrics: Optional[ContentMetrics] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
