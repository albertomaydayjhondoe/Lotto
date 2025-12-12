"""FastAPI router for Meta Creative Production Engine (PASO 10.17)"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.meta_creative_production.schemas import (
    ProductionEngineStatus, RunProductionRequest, RunProductionResponse,
    CreativeProductionRequest, VariantGenerationResult, PromotionRequest,
    PromotionResult, VariantListResponse, ProductionHistoryResponse,
    VariantGenerationConfig, RecombinationRequest, RecombinationResult
)
from app.meta_creative_production.variant_generator import AutonomousVariantGenerator
from app.meta_creative_production.recombination_engine import CreativeRecombinationEngine
from app.meta_creative_production.promotion_loop import AutoPromotionLoop
from app.meta_creative_production.fatigue_monitor import FatigueMonitor

router = APIRouter(prefix="/meta/creative-engine", tags=["Meta Creative Production"])

# ==================== STATUS ====================

@router.get("/status", response_model=ProductionEngineStatus)
async def get_production_status(
    db: Session = Depends(get_db)
):
    """Get production engine status"""
    # STUB: Return synthetic status
    return ProductionEngineStatus(
        status="running",
        last_run=datetime.utcnow(),
        next_run=datetime.utcnow(),
        total_masters=25,
        total_variants=187,
        active_variants=134,
        fatigued_variants=12,
        mode="stub"
    )

# ==================== FULL PRODUCTION RUN ====================

@router.post("/run", response_model=RunProductionResponse)
async def run_production_cycle(
    request: RunProductionRequest,
    db: Session = Depends(get_db)
):
    """Run full production cycle: generate → upload → promote top 3"""
    start_time = datetime.utcnow()
    
    # Initialize components
    generator = AutonomousVariantGenerator(mode=request.mode)
    promotion_loop = AutoPromotionLoop(mode=request.mode)
    fatigue_monitor = FatigueMonitor(mode=request.mode)
    
    # STUB: Simulate processing
    masters_processed = len(request.master_creative_ids) if request.master_creative_ids else 5
    variants_generated = masters_processed * 10  # Avg 10 per master
    variants_uploaded = int(variants_generated * 0.8) if request.auto_upload else 0
    
    # Monitor fatigue
    fatigue_result = await fatigue_monitor.monitor_all_variants()
    
    elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    return RunProductionResponse(
        production_id=uuid4(),
        masters_processed=masters_processed,
        variants_generated=variants_generated,
        variants_uploaded=variants_uploaded,
        top_3_promoted=[uuid4(), uuid4(), uuid4()] if request.promote_top_3 else [],
        fatigued_archived=fatigue_result.archived_count,
        processing_time_ms=elapsed,
        summary=f"Processed {masters_processed} masters, generated {variants_generated} variants",
        started_at=start_time,
        completed_at=datetime.utcnow()
    )

# ==================== VARIANT GENERATION ====================

@router.post("/generate/{creative_id}", response_model=VariantGenerationResult)
async def generate_variants(
    creative_id: UUID,
    request: CreativeProductionRequest,
    db: Session = Depends(get_db)
):
    """Generate variants for specific master creative"""
    
    generator = AutonomousVariantGenerator(mode=request.mode)
    config = VariantGenerationConfig()
    
    result = await generator.generate_variants(request, config)
    
    return result

# ==================== RECOMBINATION ====================

@router.post("/recombine", response_model=RecombinationResult)
async def recombine_creative(
    request: RecombinationRequest,
    db: Session = Depends(get_db)
):
    """Create recombined variants using best fragments"""
    
    engine = CreativeRecombinationEngine(mode="stub")
    result = await engine.recombine_fragments(request)
    
    return result

# ==================== VARIANT LIST ====================

@router.get("/variants/{creative_id}", response_model=VariantListResponse)
async def get_variants(
    creative_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all variants for a master creative"""
    
    # STUB: Return synthetic list
    return VariantListResponse(
        master_creative_id=creative_id,
        total_variants=12,
        active=8,
        testing=3,
        fatigued=1,
        archived=0,
        variants=[]
    )

# ==================== PROMOTION ====================

@router.post("/promote/{variant_id}", response_model=PromotionResult)
async def promote_variant(
    variant_id: UUID,
    request: PromotionRequest,
    db: Session = Depends(get_db)
):
    """Manually promote variant to Meta Ads"""
    
    promotion_loop = AutoPromotionLoop(mode="stub")
    result = await promotion_loop.upload_variant(request)
    
    return result

# ==================== HISTORY ====================

@router.get("/history", response_model=ProductionHistoryResponse)
async def get_production_history(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get full production history"""
    
    # STUB: Return synthetic history
    return ProductionHistoryResponse(
        total_runs=45,
        total_variants_generated=524,
        total_uploads=402,
        avg_variants_per_master=11.6,
        best_performing_structure="hook_body_cta",
        history=[]
    )
