"""Pydantic models for E2B sandbox simulation engine."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FakeYoloDetection(BaseModel):
    """Simulated YOLO object detection result."""
    
    class_name: str = Field(description="Detected object class (person, car, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    bbox: List[float] = Field(description="Bounding box [x, y, width, height]")
    timestamp_ms: int = Field(description="Timestamp in video (milliseconds)")


class FakeTrendFeatures(BaseModel):
    """Simulated trend analysis features."""
    
    hashtag_relevance: float = Field(ge=0.0, le=1.0, description="Trending hashtag score")
    audio_trend_score: float = Field(ge=0.0, le=1.0, description="Audio trend match score")
    visual_trend_score: float = Field(ge=0.0, le=1.0, description="Visual trend match score")
    overall_trend_score: float = Field(ge=0.0, le=1.0, description="Combined trend score")


class FakeEmbedding(BaseModel):
    """Simulated video embedding vector."""
    
    vector: List[float] = Field(description="Embedding vector (512-dimensional)")
    model_name: str = Field(default="fake-clip-vit", description="Model used for embedding")
    timestamp_ms: int = Field(description="Timestamp in video")


class FakeCut(BaseModel):
    """Simulated video cut/clip segment."""
    
    start_ms: int = Field(ge=0, description="Cut start time in milliseconds")
    end_ms: int = Field(gt=0, description="Cut end time in milliseconds")
    duration_ms: int = Field(gt=0, description="Cut duration in milliseconds")
    visual_score: float = Field(ge=0.0, le=1.0, description="Visual quality score")
    motion_intensity: float = Field(ge=0.0, le=1.0, description="Motion/action intensity")
    trend_score: float = Field(ge=0.0, le=1.0, description="Trend relevance score")
    confidence: float = Field(ge=0.0, le=1.0, description="Cut quality confidence")


class E2BSandboxRequest(BaseModel):
    """Request to launch E2B sandbox simulation."""
    
    video_asset_id: UUID
    job_id: UUID
    job_type: str = Field(default="cut_analysis_e2b")
    params: Optional[dict] = Field(default_factory=dict)


class E2BSandboxResult(BaseModel):
    """Result from E2B sandbox simulation."""
    
    job_id: UUID
    video_asset_id: UUID
    status: str = Field(description="completed, failed, etc.")
    
    # Simulated analysis results
    yolo_detections: List[FakeYoloDetection] = Field(default_factory=list)
    embeddings: List[FakeEmbedding] = Field(default_factory=list)
    trend_features: Optional[FakeTrendFeatures] = None
    cuts: List[FakeCut] = Field(default_factory=list)
    
    # Metadata
    processing_time_ms: int = Field(description="Simulated processing time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
