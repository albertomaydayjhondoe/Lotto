"""E2B sandbox simulation runner - generates fake analysis results."""

import random
import time
from uuid import uuid4
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Job, VideoAsset, Clip, ClipStatus, JobStatus
from app.e2b.models import (
    E2BSandboxResult,
    FakeYoloDetection,
    FakeTrendFeatures,
    FakeEmbedding,
    FakeCut,
)
from app.ledger import log_event


async def run_e2b_simulation(
    job: Job,
    db: AsyncSession,
) -> E2BSandboxResult:
    """
    Run complete E2B sandbox simulation for video analysis.
    
    Generates:
    - YOLO detections (10-30 objects)
    - Embeddings (every 1000ms)
    - Trend features
    - Video cuts (3-12 clips)
    - Visual scores for each cut
    
    Formula: score = 0.6*visual + 0.2*motion + 0.2*trend
    
    Args:
        job: Job object with video_asset_id
        db: Database session
    
    Returns:
        E2BSandboxResult with all simulated data
    
    Raises:
        ValueError: If video asset not found
    """
    start_time = time.time()
    
    # Load video asset
    stmt = select(VideoAsset).where(VideoAsset.id == job.video_asset_id)
    result = await db.execute(stmt)
    video_asset = result.scalar_one_or_none()
    
    if not video_asset:
        raise ValueError(f"Video asset {job.video_asset_id} not found")
    
    duration_ms = video_asset.duration_ms or 30000  # Default 30s
    
    # Generate fake YOLO detections
    yolo_detections = _generate_yolo_detections(duration_ms)
    
    # Generate fake embeddings
    embeddings = _generate_embeddings(duration_ms)
    
    # Generate fake trend features
    trend_features = _generate_trend_features()
    
    # Generate fake cuts (3-12 clips)
    cuts = _generate_cuts(duration_ms, trend_features)
    
    # Create clips in database
    await _create_clips_in_db(
        db=db,
        video_asset_id=video_asset.id,
        cuts=cuts
    )
    
    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Log to ledger
    await log_event(
        db=db,
        event_type="e2b_simulation_completed",
        entity_type="job",
        entity_id=str(job.id),
        metadata={
            "video_asset_id": str(video_asset.id),
            "num_detections": len(yolo_detections),
            "num_embeddings": len(embeddings),
            "num_cuts": len(cuts),
            "processing_time_ms": processing_time_ms
        }
    )
    
    return E2BSandboxResult(
        job_id=job.id,
        video_asset_id=video_asset.id,
        status="completed",
        yolo_detections=yolo_detections,
        embeddings=embeddings,
        trend_features=trend_features,
        cuts=cuts,
        processing_time_ms=processing_time_ms,
        created_at=datetime.utcnow()
    )


def _generate_yolo_detections(duration_ms: int) -> List[FakeYoloDetection]:
    """Generate 10-30 fake YOLO detections spread across video."""
    num_detections = random.randint(10, 30)
    detections = []
    
    classes = ["person", "car", "dog", "cat", "bicycle", "bottle", "phone", "laptop"]
    
    for _ in range(num_detections):
        detections.append(FakeYoloDetection(
            class_name=random.choice(classes),
            confidence=random.uniform(0.7, 0.99),
            bbox=[
                random.uniform(0, 800),  # x
                random.uniform(0, 600),  # y
                random.uniform(50, 300),  # width
                random.uniform(50, 300),  # height
            ],
            timestamp_ms=random.randint(0, duration_ms)
        ))
    
    return sorted(detections, key=lambda d: d.timestamp_ms)


def _generate_embeddings(duration_ms: int) -> List[FakeEmbedding]:
    """Generate embeddings every ~1000ms."""
    embeddings = []
    
    for timestamp in range(0, duration_ms, 1000):
        embeddings.append(FakeEmbedding(
            vector=[random.uniform(-1, 1) for _ in range(512)],
            model_name="fake-clip-vit",
            timestamp_ms=timestamp
        ))
    
    return embeddings


def _generate_trend_features() -> FakeTrendFeatures:
    """Generate fake trend analysis scores."""
    return FakeTrendFeatures(
        hashtag_relevance=random.uniform(0.3, 0.9),
        audio_trend_score=random.uniform(0.4, 0.95),
        visual_trend_score=random.uniform(0.5, 0.9),
        overall_trend_score=random.uniform(0.4, 0.85)
    )


def _generate_cuts(duration_ms: int, trend_features: FakeTrendFeatures) -> List[FakeCut]:
    """
    Generate 3-12 fake cuts with calculated scores.
    
    Score formula: 0.6*visual + 0.2*motion + 0.2*trend
    """
    num_cuts = random.randint(3, 12)
    cuts = []
    
    # Generate non-overlapping cuts
    min_cut_duration = 5000  # 5 seconds
    max_cut_duration = 15000  # 15 seconds
    
    # If video is too short, reduce min duration
    if duration_ms < min_cut_duration * 3:
        min_cut_duration = max(1000, duration_ms // 4)
    
    # Generate random start positions
    max_start = max(0, duration_ms - min_cut_duration)
    if max_start <= 0:
        # Video too short, create single cut
        num_cuts = 1
    
    positions = []
    for _ in range(num_cuts):
        if max_start > 0:
            positions.append(random.randint(0, max_start))
        else:
            positions.append(0)
    
    positions = sorted(set(positions))  # Remove duplicates and sort
    
    for i, start_ms in enumerate(positions):
        # Calculate maximum possible duration
        max_possible = min(max_cut_duration, duration_ms - start_ms)
        
        # Check if next position limits duration
        if i < len(positions) - 1:
            max_possible = min(max_possible, positions[i + 1] - start_ms)
        
        # Ensure max_possible >= min_cut_duration
        if max_possible < min_cut_duration:
            max_possible = min_cut_duration
        
        # Make sure we don't go past video end
        max_possible = min(max_possible, duration_ms - start_ms)
        
        # Generate duration (handle edge case where min > max)
        if max_possible >= min_cut_duration:
            duration = random.randint(min_cut_duration, max_possible)
        else:
            duration = max_possible
        
        end_ms = min(start_ms + duration, duration_ms)
        actual_duration = end_ms - start_ms
        
        # Skip if duration is too small
        if actual_duration < 1000:  # Less than 1 second
            continue
        
        # Generate component scores
        visual_score = random.uniform(0.5, 0.95)
        motion_intensity = random.uniform(0.3, 0.9)
        trend_score = trend_features.overall_trend_score * random.uniform(0.8, 1.0)
        
        # Calculate confidence (random but correlated with scores)
        confidence = (visual_score + motion_intensity + trend_score) / 3.0 * random.uniform(0.9, 1.0)
        
        cuts.append(FakeCut(
            start_ms=start_ms,
            end_ms=end_ms,
            duration_ms=actual_duration,
            visual_score=visual_score,
            motion_intensity=motion_intensity,
            trend_score=trend_score,
            confidence=min(confidence, 1.0)
        ))
    
    return sorted(cuts, key=lambda c: c.start_ms)


async def _create_clips_in_db(
    db: AsyncSession,
    video_asset_id,
    cuts: List[FakeCut],
) -> None:
    """Create Clip records in database from FakeCuts."""
    for cut in cuts:
        clip = Clip(
            id=uuid4(),
            video_asset_id=video_asset_id,
            start_ms=cut.start_ms,
            end_ms=cut.end_ms,
            duration_ms=cut.duration_ms,
            visual_score=cut.visual_score,
            status=ClipStatus.READY,
            params={
                "motion_intensity": cut.motion_intensity,
                "trend_score": cut.trend_score,
                "confidence": cut.confidence,
                "source": "e2b_simulation"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(clip)
    
    await db.commit()
