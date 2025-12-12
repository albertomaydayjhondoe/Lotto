"""
Creative Intelligence Orchestrator

Orquesta los 5 subsistemas:
1. Visual Analyzer
2. Variant Generator
3. Winner Engine
4. Thumbnail Generator
5. Lifecycle Manager
"""
import logging
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_creative_intelligence.visual_analyzer import VisualAnalyzer
from app.meta_creative_intelligence.variant_generator import VariantGenerator
from app.meta_creative_intelligence.winner_engine import WinnerEngine
from app.meta_creative_intelligence.thumbnail_generator import ThumbnailGenerator
from app.meta_creative_intelligence.lifecycle_manager import LifecycleManager
from app.meta_creative_intelligence.schemas import (
    CreativeIntelligenceRunRequest,
    CreativeIntelligenceRunResponse,
    VariantConfig,
)
from app.meta_creative_intelligence.models import (
    MetaCreativeAnalysisModel,
    MetaCreativeVariantGenerationModel,
    MetaThumbnailModel,
    MetaCreativeLifecycleModel,
)

logger = logging.getLogger(__name__)


class MetaCreativeIntelligenceOrchestrator:
    """
    Orquestador principal del sistema de inteligencia creativa.
    
    Flujo:
    1. Analizar videos (Visual Analyzer)
    2. Generar variantes (Variant Generator)
    3. Generar thumbnails (Thumbnail Generator)
    4. Detectar fatiga (Lifecycle Manager)
    5. Persistir resultados en DB
    """
    
    def __init__(self, mode: str = "stub"):
        """
        Args:
            mode: "stub" o "live"
        """
        self.mode = mode
        self.visual_analyzer = VisualAnalyzer(mode=mode)
        self.variant_generator = VariantGenerator(mode=mode)
        self.winner_engine = WinnerEngine(mode=mode)
        self.thumbnail_generator = ThumbnailGenerator(mode=mode)
        self.lifecycle_manager = LifecycleManager(mode=mode)
        
        logger.info(f"MetaCreativeIntelligenceOrchestrator initialized in {mode} mode")
    
    async def run(
        self,
        db: AsyncSession,
        video_asset_ids: list[UUID],
        enable_analysis: bool = True,
        enable_variants: bool = True,
        enable_thumbnails: bool = True,
        enable_lifecycle_check: bool = True,
    ) -> CreativeIntelligenceRunResponse:
        """
        Ejecuta el flujo completo de inteligencia creativa.
        
        Args:
            db: Database session
            video_asset_ids: IDs de videos a procesar
            enable_analysis: Ejecutar análisis visual
            enable_variants: Generar variantes
            enable_thumbnails: Generar thumbnails
            enable_lifecycle_check: Verificar fatiga
            
        Returns:
            CreativeIntelligenceRunResponse con resumen
        """
        logger.info(f"Running creative intelligence for {len(video_asset_ids)} videos")
        
        import time
        start = time.time()
        
        run_id = uuid4()
        analyses_completed = 0
        variants_generated = 0
        thumbnails_created = 0
        fatigues_detected = 0
        
        summary = {
            "analysis_results": [],
            "variant_results": [],
            "thumbnail_results": [],
            "lifecycle_results": [],
        }
        
        # Procesar cada video
        for video_asset_id in video_asset_ids:
            try:
                # STEP 1: Análisis Visual
                analysis_result = None
                if enable_analysis:
                    analysis_result = await self._run_analysis(db, video_asset_id)
                    if analysis_result:
                        analyses_completed += 1
                        summary["analysis_results"].append({
                            "video_asset_id": str(video_asset_id),
                            "analysis_id": str(analysis_result.analysis_id),
                            "overall_score": analysis_result.scoring.overall_score,
                            "fragments_extracted": len(analysis_result.fragments),
                        })
                
                # STEP 2: Generación de Variantes
                if enable_variants:
                    variant_result = await self._run_variant_generation(
                        db=db,
                        video_asset_id=video_asset_id,
                        analysis=analysis_result,
                    )
                    if variant_result:
                        variants_generated += variant_result.total_variants
                        summary["variant_results"].append({
                            "video_asset_id": str(video_asset_id),
                            "generation_id": str(variant_result.generation_id),
                            "total_variants": variant_result.total_variants,
                        })
                
                # STEP 3: Generación de Thumbnails
                if enable_thumbnails:
                    thumbnail_result = await self._run_thumbnail_generation(
                        db=db,
                        video_asset_id=video_asset_id,
                        analysis=analysis_result,
                    )
                    if thumbnail_result:
                        thumbnails_created += 1
                        summary["thumbnail_results"].append({
                            "video_asset_id": str(video_asset_id),
                            "thumbnail_id": str(thumbnail_result.thumbnail_id),
                            "selected_frame": thumbnail_result.selected_frame,
                        })
                
                # STEP 4: Verificación de Fatiga
                if enable_lifecycle_check:
                    fatigue_result = await self._run_lifecycle_check(db, video_asset_id)
                    if fatigue_result and fatigue_result.is_fatigued:
                        fatigues_detected += 1
                        summary["lifecycle_results"].append({
                            "creative_id": str(video_asset_id),
                            "is_fatigued": fatigue_result.is_fatigued,
                            "fatigue_score": fatigue_result.fatigue_score,
                            "recommendation": fatigue_result.recommendation,
                        })
            
            except Exception as e:
                logger.error(f"Error processing video {video_asset_id}: {e}")
                continue
        
        duration_ms = (time.time() - start) * 1000
        
        return CreativeIntelligenceRunResponse(
            run_id=run_id,
            video_assets_processed=len(video_asset_ids),
            analyses_completed=analyses_completed,
            variants_generated=variants_generated,
            thumbnails_created=thumbnails_created,
            fatigues_detected=fatigues_detected,
            duration_ms=duration_ms,
            summary=summary,
            created_at=datetime.utcnow(),
        )
    
    # ========================================================================
    # STEP RUNNERS
    # ========================================================================
    
    async def _run_analysis(self, db: AsyncSession, video_asset_id: UUID):
        """Ejecuta análisis visual y persiste en DB"""
        try:
            # Ejecutar análisis
            result = await self.visual_analyzer.analyze(
                video_asset_id=video_asset_id,
                detect_objects=True,
                detect_faces=True,
                detect_text=True,
                extract_fragments=True,
                max_fragments=5,
            )
            
            # Persistir en DB
            analysis_model = MetaCreativeAnalysisModel(
                id=result.analysis_id,
                video_asset_id=video_asset_id,
                mode=self.mode,
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
            
            logger.info(f"Analysis completed for video {video_asset_id}")
            return result
        
        except Exception as e:
            logger.error(f"Analysis failed for video {video_asset_id}: {e}")
            return None
    
    async def _run_variant_generation(
        self,
        db: AsyncSession,
        video_asset_id: UUID,
        analysis: Optional[any],
    ):
        """Ejecuta generación de variantes y persiste en DB"""
        try:
            # Config por defecto
            config = VariantConfig(
                reorder_fragments=True,
                add_subtitles=True,
                add_overlays=True,
                vary_music=False,  # STUB
                vary_duration=True,
                min_variants=5,
                max_variants=10,
            )
            
            # Generar variantes
            result = await self.variant_generator.generate_variants(
                video_asset_id=video_asset_id,
                config=config,
                analysis=analysis,
            )
            
            # Persistir en DB
            generation_model = MetaCreativeVariantGenerationModel(
                id=result.generation_id,
                video_asset_id=video_asset_id,
                analysis_id=analysis.analysis_id if analysis else None,
                mode=self.mode,
                config=config.model_dump(),
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
            
            logger.info(f"Generated {result.total_variants} variants for video {video_asset_id}")
            return result
        
        except Exception as e:
            logger.error(f"Variant generation failed for video {video_asset_id}: {e}")
            return None
    
    async def _run_thumbnail_generation(
        self,
        db: AsyncSession,
        video_asset_id: UUID,
        analysis: Optional[any],
    ):
        """Ejecuta generación de thumbnail y persiste en DB"""
        try:
            # Generar thumbnail
            result = await self.thumbnail_generator.generate_thumbnail(
                video_asset_id=video_asset_id,
                analysis=analysis,
                max_candidates=5,
                prefer_faces=True,
                prefer_action=True,
                avoid_text=False,
            )
            
            # Persistir en DB
            thumbnail_model = MetaThumbnailModel(
                id=result.thumbnail_id,
                video_asset_id=video_asset_id,
                analysis_id=analysis.analysis_id if analysis else None,
                mode=self.mode,
                selected_frame=result.selected_frame,
                selected_timestamp=result.selected_timestamp,
                thumbnail_url=result.thumbnail_url,
                candidates=[c.model_dump() for c in result.candidates],
                prefer_faces=True,
                prefer_action=True,
                avoid_text=False,
                reasoning=result.reasoning,
            )
            
            db.add(thumbnail_model)
            await db.commit()
            
            logger.info(f"Thumbnail created for video {video_asset_id}")
            return result
        
        except Exception as e:
            logger.error(f"Thumbnail generation failed for video {video_asset_id}: {e}")
            return None
    
    async def _run_lifecycle_check(self, db: AsyncSession, video_asset_id: UUID):
        """Ejecuta verificación de fatiga y persiste en DB"""
        try:
            # Detectar fatiga
            result = await self.lifecycle_manager.detect_fatigue(
                db=db,
                creative_id=video_asset_id,
            )
            
            # Persistir en DB
            lifecycle_model = MetaCreativeLifecycleModel(
                creative_id=video_asset_id,
                action="fatigue_detection",
                is_fatigued=result.is_fatigued,
                fatigue_score=result.fatigue_score,
                metrics_trend=result.metrics_trend,
                days_active=result.days_active,
                impressions_total=result.impressions_total,
                success=True,
                recommendation=result.recommendation,
                details={"mode": self.mode},
            )
            
            db.add(lifecycle_model)
            await db.commit()
            
            logger.info(f"Lifecycle check completed for creative {video_asset_id}")
            return result
        
        except Exception as e:
            logger.error(f"Lifecycle check failed for creative {video_asset_id}: {e}")
            return None
