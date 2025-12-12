"""
ML Storage Package - Embeddings and Metrics Storage

Provides:
- EmbeddingsStore: Store and search embeddings (FAISS/pgvector)
- ModelMetricsStore: Store performance metrics
- MetricsAggregator: Aggregate and analyze metrics
"""

from .embeddings_store import EmbeddingsStore
from .model_metrics_store import ModelMetricsStore
from .metrics_aggregator import MetricsAggregator

from .schemas import (
    StoredEmbedding,
    EmbeddingType,
    EmbeddingMetadata,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    ContentSource
)

from .schemas_metrics import (
    MetricType,
    RetentionMetrics,
    EngagementMetrics,
    ViewerBehaviorMetrics,
    DailySnapshot,
    LearningReport,
    Platform,
    ChannelType
)

__all__ = [
    # Stores
    "EmbeddingsStore",
    "ModelMetricsStore",
    "MetricsAggregator",
    
    # Embedding schemas
    "StoredEmbedding",
    "EmbeddingType",
    "EmbeddingMetadata",
    "SimilaritySearchRequest",
    "SimilaritySearchResponse",
    "ContentSource",
    
    # Metrics schemas
    "MetricType",
    "RetentionMetrics",
    "EngagementMetrics",
    "ViewerBehaviorMetrics",
    "DailySnapshot",
    "LearningReport",
    "Platform",
    "ChannelType"
]
