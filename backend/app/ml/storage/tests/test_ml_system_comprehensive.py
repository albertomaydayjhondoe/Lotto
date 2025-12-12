"""
Comprehensive tests for ML Storage & Learning System

Tests:
- EmbeddingsStore (FAISS backend)
- ModelMetricsStore
- MetricsAggregator
- DailyLearningPipeline
- ViralityPredictor
- End-to-end learning flow
"""

import pytest
import asyncio
import numpy as np
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from backend.app.ml.storage.embeddings_store import EmbeddingsStore
from backend.app.ml.storage.model_metrics_store import ModelMetricsStore
from backend.app.ml.storage.metrics_aggregator import MetricsAggregator
from backend.app.ml.pipelines.daily_learning import DailyLearningPipeline
from backend.app.ml.pipelines.virality_predictor import ViralityPredictor
from backend.app.ml.pipelines.best_time_to_post import BestTimeToPostAnalyzer

from backend.app.ml.storage.schemas import (
    StoredEmbedding,
    EmbeddingType,
    EmbeddingMetadata,
    ContentSource,
    SimilaritySearchRequest,
    BatchEmbeddingRequest,
    EmbeddingDeletionRequest
)

from backend.app.ml.storage.schemas_metrics import (
    MetricType,
    MetricsWriteRequest,
    MetricsReadRequest,
    Platform,
    ChannelType
)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def embeddings_store(temp_storage_dir):
    """Create EmbeddingsStore instance."""
    return EmbeddingsStore(
        backend="faiss",
        storage_path=temp_storage_dir,
        dimension=512
    )


@pytest.fixture
def metrics_store():
    """Create ModelMetricsStore instance (in-memory)."""
    return ModelMetricsStore(in_memory=True)


@pytest.fixture
def metrics_aggregator(metrics_store):
    """Create MetricsAggregator instance."""
    return MetricsAggregator(metrics_store)


@pytest.fixture
def daily_learning(metrics_store, metrics_aggregator):
    """Create DailyLearningPipeline instance."""
    return DailyLearningPipeline(metrics_store, metrics_aggregator)


@pytest.fixture
def virality_predictor(metrics_store):
    """Create ViralityPredictor instance."""
    return ViralityPredictor(metrics_store)


# ================== EmbeddingsStore Tests ==================

@pytest.mark.asyncio
async def test_store_single_embedding(embeddings_store):
    """Test storing a single embedding."""
    embedding = StoredEmbedding(
        embedding_id="test_001",
        embedding_type=EmbeddingType.CLIP_VISUAL,
        vector=[0.1] * 512,
        dimension=512,
        metadata=EmbeddingMetadata(
            content_id="content_001",
            content_type="video",
            source=ContentSource.VISION_ENGINE,
            views=1000,
            retention=0.75
        )
    )
    
    result = await embeddings_store.store_embedding(embedding)
    
    assert result["success"] is True
    assert result["embedding_id"] == "test_001"
    assert "faiss" in result["backend"]


@pytest.mark.asyncio
async def test_search_similar_embeddings(embeddings_store):
    """Test similarity search."""
    # Store multiple embeddings
    for i in range(10):
        vector = [float(i) / 10] * 512
        embedding = StoredEmbedding(
            embedding_id=f"test_{i:03d}",
            embedding_type=EmbeddingType.CLIP_VISUAL,
            vector=vector,
            dimension=512,
            metadata=EmbeddingMetadata(
                content_id=f"content_{i:03d}",
                content_type="video",
                source=ContentSource.VISION_ENGINE
            )
        )
        await embeddings_store.store_embedding(embedding)
    
    # Search for similar
    query_vector = [0.5] * 512
    request = SimilaritySearchRequest(
        query_vector=query_vector,
        embedding_type=EmbeddingType.CLIP_VISUAL,
        top_k=3,
        include_metadata=True
    )
    
    response = await embeddings_store.search_similar(request)
    
    assert response.total_found <= 3
    assert response.search_time_ms > 0
    assert response.index_used == "faiss"
    
    if response.results:
        assert response.results[0].similarity_score > 0
        assert response.results[0].metadata is not None


@pytest.mark.asyncio
async def test_batch_store_embeddings(embeddings_store):
    """Test batch storing embeddings."""
    embeddings = []
    for i in range(20):
        vector = [float(i) / 20] * 512
        embedding = StoredEmbedding(
            embedding_id=f"batch_{i:03d}",
            embedding_type=EmbeddingType.TEXT_CAPTION,
            vector=vector,
            dimension=512,
            metadata=EmbeddingMetadata(
                content_id=f"content_batch_{i:03d}",
                content_type="text",
                source=ContentSource.COMMUNITY_MANAGER
            )
        )
        embeddings.append(embedding)
    
    request = BatchEmbeddingRequest(
        embeddings=embeddings,
        skip_if_exists=True
    )
    
    response = await embeddings_store.batch_store(request)
    
    assert response.stored == 20
    assert response.skipped == 0
    assert response.failed == 0
    assert response.processing_time_ms > 0


@pytest.mark.asyncio
async def test_delete_embedding(embeddings_store):
    """Test deleting embeddings."""
    # Store embedding
    embedding = StoredEmbedding(
        embedding_id="test_delete",
        embedding_type=EmbeddingType.BRAND_STYLE,
        vector=[0.1] * 512,
        dimension=512,
        metadata=EmbeddingMetadata(
            content_id="content_delete",
            content_type="image",
            source=ContentSource.BRAND_ENGINE
        )
    )
    await embeddings_store.store_embedding(embedding)
    
    # Delete
    request = EmbeddingDeletionRequest(
        embedding_ids=["test_delete"],
        confirm_deletion=True
    )
    
    response = await embeddings_store.delete_embedding(request)
    
    assert response.deleted_count == 1
    assert "test_delete" in response.deleted_ids


@pytest.mark.asyncio
async def test_update_embedding_metadata(embeddings_store):
    """Test updating embedding metadata."""
    # Store embedding
    embedding = StoredEmbedding(
        embedding_id="test_update",
        embedding_type=EmbeddingType.CLIP_VISUAL,
        vector=[0.1] * 512,
        dimension=512,
        metadata=EmbeddingMetadata(
            content_id="content_update",
            content_type="video",
            source=ContentSource.VISION_ENGINE,
            views=100
        )
    )
    await embeddings_store.store_embedding(embedding)
    
    # Update
    result = await embeddings_store.update_embedding(
        "test_update",
        {"views": 1000, "retention": 0.85}
    )
    
    assert result["success"] is True
    assert "views" in result["updated_fields"]


# ================== ModelMetricsStore Tests ==================

@pytest.mark.asyncio
async def test_write_retention_metrics(metrics_store):
    """Test writing retention metrics."""
    request = MetricsWriteRequest(
        metric_type=MetricType.RETENTION,
        content_id="video_001",
        platform=Platform.TIKTOK,
        channel_type=ChannelType.OFFICIAL,
        data={
            "avg_watch_time_sec": 25.5,
            "avg_watch_percentage": 0.85,
            "retention_curve": [1.0, 0.95, 0.90, 0.85, 0.80],
            "drop_off_points": [3, 10, 25],
            "completion_rate": 0.75,
            "rewatch_rate": 0.15
        }
    )
    
    result = await metrics_store.write_metrics(request)
    
    assert result["success"] is True
    assert result["content_id"] == "video_001"


@pytest.mark.asyncio
async def test_write_engagement_metrics(metrics_store):
    """Test writing engagement metrics."""
    request = MetricsWriteRequest(
        metric_type=MetricType.ENGAGEMENT,
        content_id="video_002",
        platform=Platform.INSTAGRAM,
        channel_type=ChannelType.OFFICIAL,
        data={
            "views": 50000,
            "likes": 5000,
            "comments": 250,
            "shares": 1000,
            "saves": 2000,
            "ctr": 0.12,
            "engagement_rate": 0.165,
            "save_rate": 0.04,
            "views_velocity": 2500.0,
            "engagement_velocity": 400.0
        }
    )
    
    result = await metrics_store.write_metrics(request)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_read_metrics(metrics_store):
    """Test reading metrics."""
    # Write some metrics first
    for i in range(5):
        request = MetricsWriteRequest(
            metric_type=MetricType.RETENTION,
            content_id=f"video_{i:03d}",
            platform=Platform.TIKTOK,
            data={
                "avg_watch_time_sec": 20 + i,
                "avg_watch_percentage": 0.7 + (i * 0.05),
                "retention_curve": [1.0] * 10,
                "completion_rate": 0.6 + (i * 0.05),
                "rewatch_rate": 0.1
            }
        )
        await metrics_store.write_metrics(request)
    
    # Read metrics
    read_request = MetricsReadRequest(
        content_ids=[f"video_{i:03d}" for i in range(5)],
        metric_types=[MetricType.RETENTION]
    )
    
    result = await metrics_store.read_metrics(read_request)
    
    assert result["success"] is True
    assert len(result["metrics"]["retention"]) == 5


@pytest.mark.asyncio
async def test_write_meta_learning_score(metrics_store):
    """Test writing meta-learning scores."""
    request = MetricsWriteRequest(
        metric_type=MetricType.LEARNING_SCORE,
        content_id="video_score_001",
        data={
            "overall_score": 85.5,
            "retention_score": 90.0,
            "engagement_score": 82.0,
            "virality_score": 88.0,
            "brand_alignment_score": 92.0,
            "factors": {
                "quality": 0.9,
                "timing": 0.8,
                "aesthetic": 0.95
            },
            "strengths": ["High retention", "Strong brand alignment"],
            "weaknesses": ["Could improve CTA"],
            "improvement_suggestions": ["Add stronger hook in first 2 seconds"]
        }
    )
    
    result = await metrics_store.write_metrics(request)
    
    assert result["success"] is True


# ================== MetricsAggregator Tests ==================

@pytest.mark.asyncio
async def test_build_daily_snapshot(metrics_store, metrics_aggregator):
    """Test building daily snapshot."""
    # Write sample metrics
    target_date = date.today() - timedelta(days=1)
    
    for i in range(10):
        # Retention
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.RETENTION,
            content_id=f"snap_video_{i}",
            platform=Platform.TIKTOK,
            data={
                "avg_watch_time_sec": 20 + i,
                "avg_watch_percentage": 0.6 + (i * 0.03),
                "retention_curve": [1.0] * 10,
                "completion_rate": 0.5 + (i * 0.03),
                "rewatch_rate": 0.1
            }
        ))
        
        # Engagement
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.ENGAGEMENT,
            content_id=f"snap_video_{i}",
            platform=Platform.TIKTOK,
            data={
                "views": 10000 + (i * 1000),
                "likes": 1000 + (i * 100),
                "comments": 50 + (i * 5),
                "shares": 100 + (i * 10),
                "saves": 200 + (i * 20),
                "engagement_rate": 0.13 + (i * 0.01),
                "save_rate": 0.02,
                "views_velocity": 500.0,
                "engagement_velocity": 65.0
            }
        ))
    
    snapshot = await metrics_aggregator.build_daily_snapshot(target_date)
    
    assert snapshot.total_content_analyzed >= 10
    assert snapshot.avg_retention > 0
    assert snapshot.avg_engagement_rate > 0
    assert len(snapshot.insights) > 0
    assert len(snapshot.recommendations) > 0


@pytest.mark.asyncio
async def test_compute_retention_clusters(metrics_store, metrics_aggregator):
    """Test retention clustering."""
    # Write varied retention metrics
    for i in range(30):
        retention = 0.3 + (i / 30) * 0.6  # Range from 0.3 to 0.9
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.RETENTION,
            content_id=f"cluster_video_{i}",
            platform=Platform.TIKTOK,
            data={
                "avg_watch_time_sec": 20,
                "avg_watch_percentage": retention,
                "retention_curve": [1.0] * 10,
                "completion_rate": retention,
                "rewatch_rate": 0.1
            }
        ))
    
    clusters = await metrics_aggregator.compute_retention_clusters(min_cluster_size=3)
    
    assert len(clusters) > 0
    for cluster in clusters:
        assert cluster.content_count >= 3
        assert 0 <= cluster.avg_retention <= 1


# ================== DailyLearningPipeline Tests ==================

@pytest.mark.asyncio
async def test_daily_learning_pipeline(metrics_store, daily_learning):
    """Test complete daily learning pipeline."""
    target_date = date.today() - timedelta(days=1)
    
    # Write sample data
    for i in range(15):
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.RETENTION,
            content_id=f"learning_video_{i}",
            platform=Platform.TIKTOK,
            data={
                "avg_watch_time_sec": 25,
                "avg_watch_percentage": 0.75,
                "retention_curve": [1.0] * 30,
                "drop_off_points": [3, 15],
                "completion_rate": 0.7,
                "rewatch_rate": 0.15
            }
        ))
        
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.ENGAGEMENT,
            content_id=f"learning_video_{i}",
            platform=Platform.TIKTOK,
            data={
                "views": 25000,
                "likes": 2500,
                "comments": 150,
                "shares": 500,
                "saves": 800,
                "engagement_rate": 0.16,
                "save_rate": 0.032,
                "views_velocity": 1250.0,
                "engagement_velocity": 200.0
            }
        ))
    
    result = await daily_learning.run_daily_learning(target_date)
    
    assert result["success"] is True
    assert result["target_date"] == target_date.isoformat()
    assert "report" in result
    assert "retention_patterns" in result
    assert "content_insights" in result
    assert "recommendations" in result
    assert result["processing_time_sec"] > 0


# ================== ViralityPredictor Tests ==================

@pytest.mark.asyncio
async def test_virality_prediction(virality_predictor):
    """Test virality prediction."""
    metadata = {
        "quality_score": 0.85,
        "aesthetic_score": 0.90,
        "scene_objects": ["person", "guitar", "stage"],
        "dominant_colors": ["blue", "gold"],
        "duration": 25,
        "platform": "tiktok",
        "caption": "Amazing performance! 🎸 #music #live"
    }
    
    prediction = await virality_predictor.predict_virality("test_content_001", metadata)
    
    assert 0 <= prediction.virality_score <= 100
    assert prediction.predicted_views > 0
    assert 0 <= prediction.confidence <= 1
    assert len(prediction.factors) > 0
    assert prediction.boost_recommended in [True, False]


# ================== Integration Tests ==================

@pytest.mark.asyncio
async def test_end_to_end_learning_flow(embeddings_store, metrics_store, daily_learning, virality_predictor):
    """Test complete end-to-end learning flow."""
    # 1. Store embeddings (simulating Vision Engine output)
    for i in range(10):
        vector = np.random.rand(512).tolist()
        embedding = StoredEmbedding(
            embedding_id=f"e2e_{i}",
            embedding_type=EmbeddingType.CLIP_VISUAL,
            vector=vector,
            dimension=512,
            metadata=EmbeddingMetadata(
                content_id=f"e2e_content_{i}",
                content_type="video",
                source=ContentSource.VISION_ENGINE,
                aesthetic_score=0.7 + (i * 0.02),
                quality_score=0.75 + (i * 0.02)
            )
        )
        await embeddings_store.store_embedding(embedding)
    
    # 2. Write performance metrics (simulating real performance data)
    for i in range(10):
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.RETENTION,
            content_id=f"e2e_content_{i}",
            platform=Platform.TIKTOK,
            data={
                "avg_watch_time_sec": 22 + i,
                "avg_watch_percentage": 0.70 + (i * 0.02),
                "retention_curve": [1.0] * 30,
                "drop_off_points": [2, 12, 25],
                "completion_rate": 0.65 + (i * 0.02),
                "rewatch_rate": 0.12
            }
        ))
        
        await metrics_store.write_metrics(MetricsWriteRequest(
            metric_type=MetricType.ENGAGEMENT,
            content_id=f"e2e_content_{i}",
            platform=Platform.TIKTOK,
            data={
                "views": 30000 + (i * 2000),
                "likes": 3000 + (i * 200),
                "comments": 180,
                "shares": 600,
                "saves": 900,
                "engagement_rate": 0.15 + (i * 0.005),
                "save_rate": 0.03,
                "views_velocity": 1500.0,
                "engagement_velocity": 225.0
            }
        ))
    
    # 3. Run daily learning
    target_date = date.today() - timedelta(days=1)
    learning_result = await daily_learning.run_daily_learning(target_date)
    
    assert learning_result["success"] is True
    assert learning_result["report"] is not None
    
    # 4. Predict virality for new content
    new_metadata = {
        "quality_score": 0.88,
        "aesthetic_score": 0.92,
        "scene_objects": ["performance", "crowd", "lights"],
        "duration": 28,
        "caption": "Epic moment! 🔥"
    }
    
    prediction = await virality_predictor.predict_virality("new_content_001", new_metadata)
    
    assert prediction.virality_score > 0
    assert prediction.confidence > 0
    
    # 5. Search for similar successful content
    query_vector = np.random.rand(512).tolist()
    search_request = SimilaritySearchRequest(
        query_vector=query_vector,
        embedding_type=EmbeddingType.CLIP_VISUAL,
        top_k=5,
        include_metadata=True
    )
    
    search_response = await embeddings_store.search_similar(search_request)
    
    # Verify complete flow
    assert learning_result["retention_patterns"]["total_analyzed"] == 10
    assert len(learning_result["recommendations"]) > 0
    assert search_response.total_found <= 5


@pytest.mark.asyncio
async def test_learning_improves_over_time(metrics_store, daily_learning):
    """Test that learning accumulates over multiple days."""
    dates = [date.today() - timedelta(days=i) for i in range(7, 0, -1)]
    
    for day_idx, target_date in enumerate(dates):
        # Simulate improving performance over time
        improvement_factor = day_idx * 0.05
        
        for i in range(5):
            await metrics_store.write_metrics(MetricsWriteRequest(
                metric_type=MetricType.RETENTION,
                content_id=f"day{day_idx}_video_{i}",
                platform=Platform.TIKTOK,
                data={
                    "avg_watch_time_sec": 20 + improvement_factor * 10,
                    "avg_watch_percentage": 0.6 + improvement_factor,
                    "retention_curve": [1.0] * 30,
                    "completion_rate": 0.5 + improvement_factor,
                    "rewatch_rate": 0.1 + improvement_factor * 0.5
                }
            ))
    
    # Get learning history
    history = await daily_learning.get_learning_history(days=7)
    
    assert len(history) > 0
    
    # Verify metrics are recorded
    for entry in history:
        assert "date" in entry
        assert "avg_retention" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
