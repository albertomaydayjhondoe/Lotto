"""
Schemas for ML Storage - Embeddings and Metadata

Defines Pydantic models for:
- Embeddings (CLIP visual, text, brand)
- Metadata (content info, performance metrics)
- Search results
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np


class EmbeddingType(str, Enum):
    """Types of embeddings stored."""
    CLIP_VISUAL = "clip_visual"
    TEXT_CAPTION = "text_caption"
    TEXT_PROMPT = "text_prompt"
    TEXT_TREND = "text_trend"
    BRAND_STYLE = "brand_style"
    AUDIO_FEATURE = "audio_feature"


class ContentSource(str, Enum):
    """Source of the content."""
    VISION_ENGINE = "vision_engine"
    CONTENT_ENGINE = "content_engine"
    SATELLITE_ENGINE = "satellite_engine"
    BRAND_ENGINE = "brand_engine"
    COMMUNITY_MANAGER = "community_manager"
    USER_UPLOAD = "user_upload"


class EmbeddingMetadata(BaseModel):
    """Metadata associated with an embedding."""
    # Content identification
    content_id: str
    content_type: str  # "video", "image", "text", "audio"
    source: ContentSource
    
    # Temporal info
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content metadata
    platform: Optional[str] = None  # "tiktok", "instagram", "youtube"
    channel_type: Optional[str] = None  # "official", "satellite"
    
    # Performance metrics (if available)
    views: Optional[int] = None
    retention: Optional[float] = None
    engagement_rate: Optional[float] = None
    
    # Visual metadata (from Vision Engine)
    scene_objects: Optional[List[str]] = None
    dominant_colors: Optional[List[str]] = None
    aesthetic_score: Optional[float] = None
    quality_score: Optional[float] = None
    
    # Text metadata (from CM/Content)
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    
    # Brand metadata
    brand_compliance: Optional[float] = None
    artist_id: Optional[str] = None
    
    # Custom metadata
    extra: Dict[str, Any] = Field(default_factory=dict)


class StoredEmbedding(BaseModel):
    """Complete stored embedding with vector and metadata."""
    # Primary key
    embedding_id: str
    
    # Embedding data
    embedding_type: EmbeddingType
    vector: List[float]  # Stored as list for JSON serialization
    dimension: int
    
    # Metadata
    metadata: EmbeddingMetadata
    
    # Storage info
    index_name: Optional[str] = None  # FAISS index or pgvector table
    stored_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Status
    indexed: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SimilaritySearchRequest(BaseModel):
    """Request for similarity search."""
    query_vector: List[float]
    embedding_type: EmbeddingType
    top_k: int = 10
    
    # Filters
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    # Options
    include_metadata: bool = True
    include_distances: bool = True
    min_score: Optional[float] = None  # Minimum similarity score


class SimilaritySearchResult(BaseModel):
    """Single result from similarity search."""
    embedding_id: str
    similarity_score: float
    distance: float
    
    # Data
    embedding: Optional[StoredEmbedding] = None
    metadata: Optional[EmbeddingMetadata] = None
    
    # Ranking
    rank: int


class SimilaritySearchResponse(BaseModel):
    """Response from similarity search."""
    query_type: EmbeddingType
    results: List[SimilaritySearchResult]
    total_found: int
    search_time_ms: float
    
    # Search metadata
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    index_used: str


class BatchEmbeddingRequest(BaseModel):
    """Request for batch embedding storage."""
    embeddings: List[StoredEmbedding]
    batch_id: Optional[str] = None
    
    # Options
    skip_if_exists: bool = True
    rebuild_index: bool = False


class BatchEmbeddingResponse(BaseModel):
    """Response from batch embedding storage."""
    batch_id: str
    total_requested: int
    stored: int
    skipped: int
    failed: int
    
    # Timing
    processing_time_ms: float
    
    # Details
    failed_ids: List[str] = Field(default_factory=list)
    errors: Dict[str, str] = Field(default_factory=dict)


class IndexStats(BaseModel):
    """Statistics for an embedding index."""
    index_name: str
    embedding_type: EmbeddingType
    
    # Size
    total_embeddings: int
    dimension: int
    
    # Storage
    storage_backend: str  # "faiss" or "pgvector"
    index_size_mb: float
    
    # Performance
    avg_search_time_ms: float
    last_rebuild: Optional[datetime] = None
    
    # Health
    is_healthy: bool
    last_error: Optional[str] = None


class EmbeddingDeletionRequest(BaseModel):
    """Request to delete embeddings."""
    embedding_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    
    # Safety
    confirm_deletion: bool = False


class EmbeddingDeletionResponse(BaseModel):
    """Response from embedding deletion."""
    deleted_count: int
    deleted_ids: List[str]
    errors: Dict[str, str] = Field(default_factory=dict)
    
    # Safety
    dry_run: bool = False
