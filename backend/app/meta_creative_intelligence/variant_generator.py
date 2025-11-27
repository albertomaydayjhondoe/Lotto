"""
Variant Generator - Creative Variant Engine

Genera 5-10 variantes automáticas de un video base.
Cambios: orden fragmentos, subtítulos, overlays, música, duraciones.
"""
import logging
import random
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.meta_creative_intelligence.schemas import (
    VariantConfig,
    VariantMetadata,
    VariantGenerationResponse,
    VisualAnalysisResponse,
)

logger = logging.getLogger(__name__)


class VariantGenerator:
    """
    Genera variantes creativas automáticamente.
    
    STUB Mode: Simula generación de variantes
    LIVE Mode: TODO - Integrar FFmpeg para edición real
    """
    
    def __init__(self, mode: str = "stub"):
        """
        Args:
            mode: "stub" o "live"
        """
        self.mode = mode
        logger.info(f"VariantGenerator initialized in {mode} mode")
    
    async def generate_variants(
        self,
        video_asset_id: UUID,
        config: VariantConfig,
        analysis: Optional[VisualAnalysisResponse] = None,
    ) -> VariantGenerationResponse:
        """
        Genera variantes del video base.
        
        Args:
            video_asset_id: ID del video base
            config: Configuración de generación
            analysis: Análisis visual previo (opcional)
            
        Returns:
            VariantGenerationResponse con todas las variantes generadas
        """
        logger.info(f"Generating variants for video {video_asset_id} in {self.mode} mode")
        
        import time
        start = time.time()
        
        variants = []
        num_variants = random.randint(config.min_variants, config.max_variants)
        
        for i in range(num_variants):
            variant = await self._generate_single_variant(
                video_asset_id=video_asset_id,
                variant_number=i + 1,
                config=config,
                analysis=analysis,
            )
            variants.append(variant)
        
        processing_time = (time.time() - start) * 1000
        
        return VariantGenerationResponse(
            generation_id=uuid4(),
            video_asset_id=video_asset_id,
            variants=variants,
            total_variants=len(variants),
            processing_time_ms=processing_time,
            created_at=datetime.utcnow(),
        )
    
    async def _generate_single_variant(
        self,
        video_asset_id: UUID,
        variant_number: int,
        config: VariantConfig,
        analysis: Optional[VisualAnalysisResponse],
    ) -> VariantMetadata:
        """Genera una única variante"""
        changes = {}
        duration = random.uniform(10.0, 45.0)  # Base duration
        
        # 1. Reorder fragments
        if config.reorder_fragments:
            changes["reorder"] = await self._apply_reorder(analysis)
            # Slight duration change due to reorder
            duration *= random.uniform(0.95, 1.05)
        
        # 2. Add subtitles
        if config.add_subtitles:
            changes["subtitles"] = await self._apply_subtitles()
        
        # 3. Add overlays
        if config.add_overlays:
            changes["overlays"] = await self._apply_overlays()
        
        # 4. Vary music (STUB only)
        if config.vary_music:
            changes["music"] = await self._apply_music_change()
        
        # 5. Vary duration
        if config.vary_duration:
            duration_change = await self._apply_duration_change()
            changes["duration_adjustment"] = duration_change
            duration *= duration_change
        
        # Calculate estimated score
        # More changes = potentially higher score (up to a point)
        base_score = 65.0
        change_bonus = len(changes) * 3.5
        randomness = random.uniform(-5, 10)
        estimated_score = min(base_score + change_bonus + randomness, 95.0)
        
        # Asset URL (STUB)
        asset_url = None
        if self.mode == "stub":
            asset_url = f"https://cdn.example.com/variants/{video_asset_id}/variant_{variant_number}.mp4"
        
        return VariantMetadata(
            variant_number=variant_number,
            changes=changes,
            duration_seconds=duration,
            estimated_score=estimated_score,
            asset_url=asset_url,
        )
    
    # ========================================================================
    # TRANSFORMATION METHODS
    # ========================================================================
    
    async def _apply_reorder(self, analysis: Optional[VisualAnalysisResponse]) -> dict:
        """Reordena fragmentos del video"""
        strategies = [
            "hook_first",  # Mejor fragmento al inicio
            "climax_middle",  # Clímax en medio
            "reversed",  # Invertir orden
            "best_segments_only",  # Solo top 3 segmentos
        ]
        
        selected_strategy = random.choice(strategies)
        
        result = {
            "strategy": selected_strategy,
            "fragments_reordered": random.randint(2, 5),
        }
        
        if analysis and analysis.fragments:
            # Usar fragmentos reales del análisis
            result["used_analysis_fragments"] = len(analysis.fragments)
            result["top_fragment_score"] = max(f.score for f in analysis.fragments)
        
        return result
    
    async def _apply_subtitles(self) -> dict:
        """Añade subtítulos automáticos"""
        styles = ["bottom", "top", "karaoke", "highlighted"]
        
        return {
            "style": random.choice(styles),
            "language": "es",
            "font_size": random.choice([16, 18, 20, 22]),
            "color": random.choice(["white", "yellow", "cyan"]),
        }
    
    async def _apply_overlays(self) -> dict:
        """Añade overlays de texto dinámicos"""
        overlay_types = [
            {"type": "cta", "text": "¡COMPRA AHORA!", "position": "bottom_center"},
            {"type": "discount", "text": "50% OFF", "position": "top_right"},
            {"type": "urgency", "text": "ÚLTIMAS UNIDADES", "position": "top_left"},
            {"type": "brand", "text": "LOGO", "position": "top_center"},
        ]
        
        selected_overlays = random.sample(overlay_types, k=random.randint(1, 3))
        
        return {
            "overlays": selected_overlays,
            "total_overlays": len(selected_overlays),
        }
    
    async def _apply_music_change(self) -> dict:
        """Cambia la música de fondo"""
        music_genres = [
            "upbeat_electronic",
            "calm_acoustic",
            "energetic_rock",
            "corporate_motivational",
            "urban_hiphop",
        ]
        
        return {
            "genre": random.choice(music_genres),
            "replaced": True,
            "fade_in_seconds": 1.0,
            "fade_out_seconds": 1.5,
        }
    
    async def _apply_duration_change(self) -> float:
        """Cambia la duración del video"""
        adjustment_types = ["speed_up", "slow_down", "trim_start", "trim_end", "no_change"]
        adjustment_type = random.choice(adjustment_types)
        
        adjustment_map = {
            "speed_up": random.uniform(1.05, 1.25),  # 5-25% faster
            "slow_down": random.uniform(0.8, 0.95),  # 5-20% slower
            "trim_start": random.uniform(0.90, 0.98),  # Trim 2-10% del inicio
            "trim_end": random.uniform(0.90, 0.98),  # Trim 2-10% del final
            "no_change": 1.0,
        }
        
        return adjustment_map[adjustment_type]
