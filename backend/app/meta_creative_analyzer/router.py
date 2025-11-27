"""FastAPI Router for Meta Creative Analyzer (PASO 10.15)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import uuid, random
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.auth import require_role
from app.meta_creative_analyzer import schemas
from app.meta_creative_analyzer.core import CreativeIntelligenceCore
from app.meta_creative_analyzer.fatigue import FatigueDetector
from app.meta_creative_analyzer.variant_generator import CreativeVariantGenerator
from app.meta_creative_analyzer.recombination import CreativeRecombinationEngine
from app.meta_creative_analyzer.models import (
    MetaCreativeAnalysisModel, MetaCreativeHealthLogModel
)

router = APIRouter()

@router.post("/analyze/{creative_id}", response_model=schemas.AnalyzeCreativeResponse)
async def analyze_creative(
    creative_id: UUID,
    request: schemas.AnalyzeCreativeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """Analyze creative performance and detect fatigue."""
    start_time = datetime.utcnow()
    
    # Generate synthetic metrics (STUB mode)
    metrics = schemas.CreativePerformanceMetrics(
        ctr=random.uniform(0.5, 4.5), cvr=random.uniform(0.3, 6.0),
        cpc=random.uniform(0.5, 3.5), cpm=random.uniform(5, 35),
        roas=random.uniform(1.2, 4.5), video_3s=random.uniform(40, 85),
        video_25pct=random.uniform(30, 70), video_50pct=random.uniform(20, 50),
        video_100pct=random.uniform(10, 30), engagement_rate=random.uniform(2, 8),
        impressions=random.randint(5000, 100000), clicks=random.randint(100, 3000),
        conversions=random.randint(10, 200), spend=random.uniform(100, 2000)
    )
    
    # Calculate score
    core = CreativeIntelligenceCore(mode=request.mode)
    fatigue_result = None
    fatigue_penalty = 0.0
    
    if request.include_fatigue_check:
        detector = FatigueDetector(mode=request.mode)
        fatigue_result = await detector.detect_fatigue(
            creative_id, metrics, days_active=random.randint(7, 45),
            impressions_total=metrics.impressions
        )
        fatigue_penalty = fatigue_result.fatigue_score * 0.5 if fatigue_result.is_fatigued else 0.0
    
    score = await core.calculate_creative_score(metrics, fatigue_penalty)
    
    processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    return schemas.AnalyzeCreativeResponse(
        analysis_id=uuid.uuid4(), creative_id=creative_id, metrics=metrics,
        score=score, fatigue=fatigue_result, analyzed_at=datetime.utcnow(),
        processing_time_ms=processing_time
    )

@router.get("/health/{creative_id}", response_model=schemas.CreativeHealthResponse)
async def get_creative_health(
    creative_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """Get creative health status."""
    # Stub response
    is_fatigued = random.choice([True, False])
    fatigue_level = random.choice(["healthy", "mild", "moderate"]) if not is_fatigued else random.choice(["moderate", "severe", "critical"])
    overall_score = random.uniform(40, 95) if not is_fatigued else random.uniform(20, 60)
    
    return schemas.CreativeHealthResponse(
        creative_id=creative_id,
        health_status="healthy" if overall_score > 60 else "warning" if overall_score > 40 else "critical",
        overall_score=overall_score, is_fatigued=is_fatigued, fatigue_level=fatigue_level,
        recommendation="Continue monitoring" if not is_fatigued else "Refresh creative recommended",
        last_checked=datetime.utcnow()
    )

@router.post("/recombine/{creative_id}", response_model=schemas.RecombineResponse)
async def recombine_creative(
    creative_id: UUID,
    request: schemas.RecombineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """Recombine creative to generate new variants."""
    start_time = datetime.utcnow()
    
    engine = CreativeRecombinationEngine(mode=request.mode)
    result = await engine.recombine([creative_id], request.num_variants, request.strategy)
    
    return schemas.RecombineResponse(
        recombination_id=result.recombination_id, creative_id=creative_id,
        variants=result.generated_variants, total_variants=result.total_variants,
        best_variant_id=result.generated_variants[0].variant_id if result.generated_variants else uuid.uuid4(),
        processing_time_ms=result.processing_time_ms
    )

@router.post("/refresh-all", response_model=schemas.RefreshAllResponse)
async def refresh_all_fatigued(
    request: schemas.RefreshAllRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """Refresh all fatigued creatives."""
    start_time = datetime.utcnow()
    
    # Stub: simulate analyzing 10 creatives
    total_analyzed = 10
    fatigued_count = random.randint(2, 5)
    refreshed_count = fatigued_count if request.auto_apply else 0
    
    fatigued_ids = [uuid.uuid4() for _ in range(fatigued_count)]
    recommendations = [f"Refresh creative {i+1} with new variants" for i in range(fatigued_count)]
    
    processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    return schemas.RefreshAllResponse(
        total_analyzed=total_analyzed, fatigued_count=fatigued_count,
        refreshed_count=refreshed_count, fatigued_creatives=fatigued_ids,
        recommendations=recommendations, processing_time_ms=processing_time
    )

@router.get("/recommendations", response_model=schemas.RecommendationsResponse)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "manager"])),
):
    """Get all creative recommendations."""
    # Stub: generate 5 recommendations
    recommendations = []
    for i in range(5):
        urgency = random.choice(["low", "medium", "high", "critical"])
        recommendations.append(schemas.CreativeRecommendation(
            creative_id=uuid.uuid4(),
            recommendation_type=random.choice(["refresh", "pause", "boost", "optimize"]),
            urgency=urgency, current_score=random.uniform(20, 80),
            expected_improvement=random.uniform(5, 30),
            actions=["Generate 5 new variants", "Test top 3 variants"],
            reasoning=f"Creative showing signs of fatigue ({urgency} urgency)",
            created_at=datetime.utcnow()
        ))
    
    critical_count = sum(1 for r in recommendations if r.urgency == "critical")
    high_count = sum(1 for r in recommendations if r.urgency == "high")
    medium_count = sum(1 for r in recommendations if r.urgency == "medium")
    
    return schemas.RecommendationsResponse(
        total_recommendations=len(recommendations), critical_count=critical_count,
        high_count=high_count, medium_count=medium_count, recommendations=recommendations
    )

@router.get("/health-check", response_model=schemas.HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return schemas.HealthCheckResponse(
        status="healthy",
        components={"core": "ok", "fatigue_detector": "ok", "variant_generator": "ok", "recombination": "ok"},
        timestamp=datetime.utcnow()
    )
