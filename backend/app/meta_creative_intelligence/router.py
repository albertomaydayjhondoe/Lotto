"""
REST API Router para Meta Creative Intelligence System
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.auth import require_role
from app.meta_creative_intelligence.orchestrator import MetaCreativeIntelligenceOrchestrator
from app.meta_creative_intelligence.visual_analyzer import VisualAnalyzer
from app.meta_creative_intelligence.variant_generator import VariantGenerator
from app.meta_creative_intelligence.winner_engine import WinnerEngine
from app.meta_creative_intelligence.thumbnail_generator import ThumbnailGenerator
from app.meta_creative_intelligence.lifecycle_manager import LifecycleManager
from app.meta_creative_intelligence.schemas import (
    VisualAnalysisRequest,
    VisualAnalysisResponse,
    VariantGenerationRequest,
    VariantGenerationResponse,
    WinnerSelectionRequest,
    WinnerSelectionResponse,
    ThumbnailGenerationRequest,
    ThumbnailGenerationResponse,
    RenewalRequest,
    RenewalResponse,
    LifecycleHistoryResponse,
    CreativeIntelligenceRunRequest,
    CreativeIntelligenceRunResponse,
    HealthCheckResponse,
)
from app.meta_creative_intelligence.models import (
    MetaCreativeAnalysisModel,
    MetaCreativeVariantGenerationModel,
    MetaPublicationWinnerModel,
    MetaThumbnailModel,
    MetaCreativeLifecycleModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta/creative-intelligence", tags=["meta_creative_intelligence"])


# ============================================================================
# 1. VISUAL ANALYSIS
# ============================================================================

@router.post("/analyze", response_model=VisualAnalysisResponse)
async def analyze_video(
    request: VisualAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Analiza un video con computer vision.
    
    Detecta: objetos, rostros, texto, scoring visual, fragmentos.
    """
    try:
        analyzer = VisualAnalyzer(mode=request.mode)
        
        result = await analyzer.analyze(
            video_asset_id=request.video_asset_id,
            detect_objects=request.detect_objects,
            detect_faces=request.detect_faces,
            detect_text=request.detect_text,
            extract_fragments=request.extract_fragments,
            max_fragments=request.max_fragments,
        )
        
        # Persistir en DB
        analysis_model = MetaCreativeAnalysisModel(
            id=result.analysis_id,
            video_asset_id=request.video_asset_id,
            mode=request.mode,
            objects_detected=[obj.model_dump() for obj in result.objects],
            faces_detected=[face.model_dump() for face in result.faces],
            texts_detected=[text.model_dump() for text in result.texts],
            visual_scoring=result.scoring.model_dump(),
            fragments_extracted=[frag.model_dump() for frag in result.fragments],
            total_objects=len(result.objects),
            total_faces=len(result.faces),
            total_texts=len(result.texts),
            total_fragments=len(result.fragments),
            overall_score=result.scoring.overall_score,
            processing_time_ms=result.processing_time_ms,
            success=True,
        )
        
        db.add(analysis_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. VARIANT GENERATION
# ============================================================================

@router.post("/generate-variants", response_model=VariantGenerationResponse)
async def generate_variants(
    request: VariantGenerationRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Genera variantes de un video.
    
    Cambios: reorder, subtitles, overlays, music (stub), duration.
    """
    try:
        generator = VariantGenerator(mode=request.mode)
        
        # Buscar análisis previo si se proporciona
        analysis = None
        if request.analysis_id:
            stmt = select(MetaCreativeAnalysisModel).where(
                MetaCreativeAnalysisModel.id == request.analysis_id
            )
            result_db = await db.execute(stmt)
            analysis_model = result_db.scalar_one_or_none()
            if analysis_model:
                # Reconstruir VisualAnalysisResponse desde DB
                from app.meta_creative_intelligence.schemas import (
                    ObjectDetection, FaceDetection, TextDetection,
                    VisualScoring, FragmentExtraction
                )
                analysis = VisualAnalysisResponse(
                    analysis_id=analysis_model.id,
                    video_asset_id=analysis_model.video_asset_id,
                    mode=analysis_model.mode,
                    objects=[ObjectDetection(**obj) for obj in analysis_model.objects_detected or []],
                    faces=[FaceDetection(**face) for face in analysis_model.faces_detected or []],
                    texts=[TextDetection(**text) for text in analysis_model.texts_detected or []],
                    scoring=VisualScoring(**analysis_model.visual_scoring) if analysis_model.visual_scoring else VisualScoring(overall_score=0, face_score=0, action_score=0, text_score=0, color_score=0, composition_score=0, engagement_potential=0),
                    fragments=[FragmentExtraction(**frag) for frag in analysis_model.fragments_extracted or []],
                    processing_time_ms=analysis_model.processing_time_ms or 0,
                    created_at=analysis_model.created_at,
                )
        
        result = await generator.generate_variants(
            video_asset_id=request.video_asset_id,
            config=request.config,
            analysis=analysis,
        )
        
        # Persistir en DB
        generation_model = MetaCreativeVariantGenerationModel(
            id=result.generation_id,
            video_asset_id=request.video_asset_id,
            analysis_id=request.analysis_id,
            mode=request.mode,
            config=request.config.model_dump(),
            variants=[v.model_dump() for v in result.variants],
            total_variants=result.total_variants,
            variants_with_reorder=sum(1 for v in result.variants if "reorder" in v.changes),
            variants_with_subtitles=sum(1 for v in result.variants if "subtitles" in v.changes),
            variants_with_overlays=sum(1 for v in result.variants if "overlays" in v.changes),
            variants_with_music_change=sum(1 for v in result.variants if "music" in v.changes),
            processing_time_ms=result.processing_time_ms,
            success=True,
        )
        
        db.add(generation_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. WINNER SELECTION
# ============================================================================

@router.post("/select-winner", response_model=WinnerSelectionResponse)
async def select_winner(
    request: WinnerSelectionRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Selecciona el creative ganador para publicación.
    
    Basado en: ROAS, CTR, CVR, ViewDepth.
    """
    try:
        engine = WinnerEngine(mode="stub")  # TODO: mode from config
        
        result = await engine.select_winner(
            db=db,
            campaign_id=request.campaign_id,
            candidate_asset_ids=request.candidate_asset_ids,
            criteria_weights=request.criteria_weights,
            min_impressions=request.min_impressions,
        )
        
        # Persistir en DB
        winner_model = MetaPublicationWinnerModel(
            id=result.selection_id,
            campaign_id=request.campaign_id,
            winner_asset_id=result.winner_asset_id,
            runner_up_asset_id=result.runner_up_asset_id,
            criteria_weights=request.criteria_weights,
            min_impressions=request.min_impressions,
            winner_score=result.winner_score,
            runner_up_score=result.runner_up_score,
            all_scores=result.all_scores,
            performance_summary=result.performance_summary,
            reasoning=result.reasoning,
            published=False,
        )
        
        db.add(winner_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error selecting winner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. THUMBNAIL GENERATION
# ============================================================================

@router.post("/generate-thumbnail", response_model=ThumbnailGenerationResponse)
async def generate_thumbnail(
    request: ThumbnailGenerationRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Genera thumbnail automático.
    
    Heurísticas: rostros > acción > texto.
    """
    try:
        generator = ThumbnailGenerator(mode=request.mode)
        
        # Buscar análisis previo
        analysis = None
        if request.analysis_id:
            stmt = select(MetaCreativeAnalysisModel).where(
                MetaCreativeAnalysisModel.id == request.analysis_id
            )
            result_db = await db.execute(stmt)
            analysis_model = result_db.scalar_one_or_none()
            if analysis_model:
                from app.meta_creative_intelligence.schemas import (
                    ObjectDetection, FaceDetection, TextDetection,
                    VisualScoring, FragmentExtraction
                )
                analysis = VisualAnalysisResponse(
                    analysis_id=analysis_model.id,
                    video_asset_id=analysis_model.video_asset_id,
                    mode=analysis_model.mode,
                    objects=[ObjectDetection(**obj) for obj in analysis_model.objects_detected or []],
                    faces=[FaceDetection(**face) for face in analysis_model.faces_detected or []],
                    texts=[TextDetection(**text) for text in analysis_model.texts_detected or []],
                    scoring=VisualScoring(**analysis_model.visual_scoring) if analysis_model.visual_scoring else VisualScoring(overall_score=0, face_score=0, action_score=0, text_score=0, color_score=0, composition_score=0, engagement_potential=0),
                    fragments=[FragmentExtraction(**frag) for frag in analysis_model.fragments_extracted or []],
                    processing_time_ms=analysis_model.processing_time_ms or 0,
                    created_at=analysis_model.created_at,
                )
        
        result = await generator.generate_thumbnail(
            video_asset_id=request.video_asset_id,
            analysis=analysis,
            max_candidates=request.max_candidates,
            prefer_faces=request.prefer_faces,
            prefer_action=request.prefer_action,
            avoid_text=request.avoid_text,
        )
        
        # Persistir en DB
        thumbnail_model = MetaThumbnailModel(
            id=result.thumbnail_id,
            video_asset_id=request.video_asset_id,
            analysis_id=request.analysis_id,
            mode=request.mode,
            selected_frame=result.selected_frame,
            selected_timestamp=result.selected_timestamp,
            thumbnail_url=result.thumbnail_url,
            candidates=[c.model_dump() for c in result.candidates],
            prefer_faces=request.prefer_faces,
            prefer_action=request.prefer_action,
            avoid_text=request.avoid_text,
            reasoning=result.reasoning,
        )
        
        db.add(thumbnail_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. LIFECYCLE MANAGEMENT
# ============================================================================

@router.get("/check-fatigue/{creative_id}")
async def check_fatigue(
    creative_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Detecta fatiga de un creative.
    """
    try:
        manager = LifecycleManager(mode="stub")  # TODO: mode from config
        
        result = await manager.detect_fatigue(db=db, creative_id=creative_id)
        
        # Persistir en DB
        lifecycle_model = MetaCreativeLifecycleModel(
            creative_id=creative_id,
            action="fatigue_detection",
            is_fatigued=result.is_fatigued,
            fatigue_score=result.fatigue_score,
            metrics_trend=result.metrics_trend,
            days_active=result.days_active,
            impressions_total=result.impressions_total,
            success=True,
            recommendation=result.recommendation,
        )
        
        db.add(lifecycle_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error checking fatigue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/renew-creative", response_model=RenewalResponse)
async def renew_creative(
    request: RenewalRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Renueva un creative fatigado.
    
    Estrategias: generate_variant, replace_entirely, refresh_targeting.
    """
    try:
        manager = LifecycleManager(mode="stub")  # TODO: mode from config
        
        result = await manager.renew_creative(
            db=db,
            creative_id=request.creative_id,
            strategy=request.strategy,
            auto_apply=request.auto_apply,
        )
        
        # Persistir en DB
        lifecycle_model = MetaCreativeLifecycleModel(
            creative_id=request.creative_id,
            action="renewal",
            strategy=request.strategy,
            new_creative_id=result.new_creative_id,
            actions_taken=result.actions_taken,
            success=result.success,
            message=result.message,
        )
        
        db.add(lifecycle_model)
        await db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error renewing creative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lifecycle-history/{creative_id}", response_model=List[LifecycleHistoryResponse])
async def get_lifecycle_history(
    creative_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Obtiene historial de lifecycle de un creative.
    """
    try:
        stmt = (
            select(MetaCreativeLifecycleModel)
            .where(MetaCreativeLifecycleModel.creative_id == creative_id)
            .order_by(desc(MetaCreativeLifecycleModel.created_at))
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        return [
            LifecycleHistoryResponse(
                lifecycle_id=record.id,
                creative_id=record.creative_id,
                action=record.action,
                details=record.details or {},
                success=record.success,
                created_at=record.created_at,
            )
            for record in records
        ]
    
    except Exception as e:
        logger.error(f"Error getting lifecycle history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. ORCHESTRATOR
# ============================================================================

@router.post("/run", response_model=CreativeIntelligenceRunResponse)
async def run_orchestrator(
    request: CreativeIntelligenceRunRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(["admin", "manager"])),
):
    """
    Ejecuta el orchestrator completo.
    
    Procesa: análisis, variantes, thumbnails, lifecycle.
    """
    try:
        orchestrator = MetaCreativeIntelligenceOrchestrator(mode=request.mode)
        
        result = await orchestrator.run(
            db=db,
            video_asset_ids=request.video_asset_ids,
            enable_analysis=request.enable_analysis,
            enable_variants=request.enable_variants,
            enable_thumbnails=request.enable_thumbnails,
            enable_lifecycle_check=request.enable_lifecycle_check,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error running orchestrator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. HEALTH CHECK
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    """
    from datetime import datetime
    
    subsystems = {
        "visual_analyzer": "ok",
        "variant_generator": "ok",
        "winner_engine": "ok",
        "thumbnail_generator": "ok",
        "lifecycle_manager": "ok",
    }
    
    return HealthCheckResponse(
        status="healthy",
        subsystems=subsystems,
        timestamp=datetime.utcnow(),
    )
