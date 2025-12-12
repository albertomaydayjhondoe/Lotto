"""
Thumbnail Generator - Auto-Thumbnailing Layer

Genera thumbnails automáticamente detectando mejores frames.
Heurísticas: rostros > acción > texto.
"""
import logging
import random
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.meta_creative_intelligence.schemas import (
    ThumbnailCandidate,
    ThumbnailGenerationRequest,
    ThumbnailGenerationResponse,
    VisualAnalysisResponse,
)

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """
    Genera thumbnails inteligentes.
    
    STUB Mode: Simula selección de frames
    LIVE Mode: TODO - Integrar CV para detección real
    """
    
    def __init__(self, mode: str = "stub"):
        """
        Args:
            mode: "stub" o "live"
        """
        self.mode = mode
        logger.info(f"ThumbnailGenerator initialized in {mode} mode")
    
    async def generate_thumbnail(
        self,
        video_asset_id: UUID,
        analysis: Optional[VisualAnalysisResponse] = None,
        max_candidates: int = 5,
        prefer_faces: bool = True,
        prefer_action: bool = True,
        avoid_text: bool = False,
    ) -> ThumbnailGenerationResponse:
        """
        Genera thumbnail óptimo.
        
        Args:
            video_asset_id: ID del video
            analysis: Análisis visual previo (opcional)
            max_candidates: Máximo de candidatos a evaluar
            prefer_faces: Priorizar frames con rostros
            prefer_action: Priorizar frames con acción
            avoid_text: Evitar frames con mucho texto
            
        Returns:
            ThumbnailGenerationResponse con thumbnail seleccionado
        """
        logger.info(f"Generating thumbnail for video {video_asset_id} in {self.mode} mode")
        
        # 1. Generar candidatos
        candidates = await self._generate_candidates(
            video_asset_id=video_asset_id,
            analysis=analysis,
            max_candidates=max_candidates,
            prefer_faces=prefer_faces,
            prefer_action=prefer_action,
            avoid_text=avoid_text,
        )
        
        # 2. Seleccionar mejor candidato
        selected = max(candidates, key=lambda c: c.score)
        
        # 3. Generar URL (STUB)
        thumbnail_url = None
        if self.mode == "stub":
            thumbnail_url = f"https://cdn.example.com/thumbnails/{video_asset_id}/frame_{selected.frame_number}.jpg"
        
        # 4. Generar reasoning
        reasoning = await self._generate_reasoning(selected, prefer_faces, prefer_action, avoid_text)
        
        return ThumbnailGenerationResponse(
            thumbnail_id=uuid4(),
            video_asset_id=video_asset_id,
            selected_frame=selected.frame_number,
            selected_timestamp=selected.timestamp_seconds,
            thumbnail_url=thumbnail_url,
            candidates=candidates,
            reasoning=reasoning,
            created_at=datetime.utcnow(),
        )
    
    # ========================================================================
    # CANDIDATE GENERATION
    # ========================================================================
    
    async def _generate_candidates(
        self,
        video_asset_id: UUID,
        analysis: Optional[VisualAnalysisResponse],
        max_candidates: int,
        prefer_faces: bool,
        prefer_action: bool,
        avoid_text: bool,
    ) -> list[ThumbnailCandidate]:
        """Genera candidatos a thumbnail"""
        candidates = []
        
        # Si hay análisis, usar frames con detecciones
        if analysis and (analysis.faces or analysis.objects):
            candidates = await self._generate_from_analysis(
                analysis=analysis,
                max_candidates=max_candidates,
                prefer_faces=prefer_faces,
                prefer_action=prefer_action,
                avoid_text=avoid_text,
            )
        else:
            # Generar candidatos sintéticos
            candidates = await self._generate_stub_candidates(
                video_asset_id=video_asset_id,
                max_candidates=max_candidates,
                prefer_faces=prefer_faces,
                prefer_action=prefer_action,
                avoid_text=avoid_text,
            )
        
        return candidates
    
    async def _generate_from_analysis(
        self,
        analysis: VisualAnalysisResponse,
        max_candidates: int,
        prefer_faces: bool,
        prefer_action: bool,
        avoid_text: bool,
    ) -> list[ThumbnailCandidate]:
        """Genera candidatos usando análisis visual"""
        candidates = []
        
        # Frames con rostros (alta prioridad)
        if prefer_faces and analysis.faces:
            for face in analysis.faces[:max_candidates]:
                score = 85.0 + random.uniform(0, 10)
                if face.emotion == "happy":
                    score += 5
                
                candidates.append(ThumbnailCandidate(
                    frame_number=face.frame_number,
                    timestamp_seconds=face.frame_number / 30.0,  # Assuming 30 fps
                    score=min(score, 100),
                    features={
                        "face_confidence": face.confidence,
                        "emotion": face.emotion,
                        "age_range": face.age_range,
                    },
                    has_face=True,
                    has_action=False,
                    has_text=False,
                ))
        
        # Frames con acción (personas)
        if prefer_action and analysis.objects:
            persons = [o for o in analysis.objects if o.label == "person"]
            for person in persons[:max_candidates]:
                score = 70.0 + random.uniform(0, 15)
                
                candidates.append(ThumbnailCandidate(
                    frame_number=person.frame_number,
                    timestamp_seconds=person.frame_number / 30.0,
                    score=min(score, 100),
                    features={
                        "object_confidence": person.confidence,
                        "label": person.label,
                    },
                    has_face=False,
                    has_action=True,
                    has_text=False,
                ))
        
        # Frames con texto (baja prioridad si avoid_text)
        if analysis.texts:
            for text in analysis.texts[:max_candidates]:
                score = 50.0 + random.uniform(0, 20)
                if avoid_text:
                    score *= 0.5  # Penalizar
                
                candidates.append(ThumbnailCandidate(
                    frame_number=text.frame_number,
                    timestamp_seconds=text.frame_number / 30.0,
                    score=min(score, 100),
                    features={
                        "text": text.text,
                        "text_confidence": text.confidence,
                    },
                    has_face=False,
                    has_action=False,
                    has_text=True,
                ))
        
        # Ordenar por score y limitar
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:max_candidates]
    
    async def _generate_stub_candidates(
        self,
        video_asset_id: UUID,
        max_candidates: int,
        prefer_faces: bool,
        prefer_action: bool,
        avoid_text: bool,
    ) -> list[ThumbnailCandidate]:
        """STUB: Genera candidatos sintéticos"""
        candidates = []
        
        for i in range(max_candidates):
            frame_number = random.randint(30, 300)  # Entre 1s y 10s
            
            # Características aleatorias
            has_face = random.random() < 0.6 if prefer_faces else random.random() < 0.3
            has_action = random.random() < 0.5 if prefer_action else random.random() < 0.3
            has_text = random.random() < 0.2 if not avoid_text else random.random() < 0.05
            
            # Score basado en características
            score = 50.0
            if has_face:
                score += 30.0
            if has_action:
                score += 15.0
            if has_text and not avoid_text:
                score += 5.0
            elif has_text and avoid_text:
                score -= 10.0
            
            score += random.uniform(-5, 10)
            score = max(0, min(100, score))
            
            candidates.append(ThumbnailCandidate(
                frame_number=frame_number,
                timestamp_seconds=frame_number / 30.0,
                score=score,
                features={
                    "synthetic": True,
                },
                has_face=has_face,
                has_action=has_action,
                has_text=has_text,
            ))
        
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates
    
    # ========================================================================
    # REASONING
    # ========================================================================
    
    async def _generate_reasoning(
        self,
        selected: ThumbnailCandidate,
        prefer_faces: bool,
        prefer_action: bool,
        avoid_text: bool,
    ) -> str:
        """Genera explicación de la selección"""
        reasons = []
        
        if selected.has_face:
            reasons.append("contains face(s)")
        if selected.has_action:
            reasons.append("shows action/movement")
        if selected.has_text and not avoid_text:
            reasons.append("includes promotional text")
        
        config_str = []
        if prefer_faces:
            config_str.append("prioritizing faces")
        if prefer_action:
            config_str.append("prioritizing action")
        if avoid_text:
            config_str.append("avoiding text")
        
        reasoning = (
            f"Selected frame {selected.frame_number} at {selected.timestamp_seconds:.1f}s "
            f"with score {selected.score:.1f}/100. "
        )
        
        if reasons:
            reasoning += f"Features: {', '.join(reasons)}. "
        
        if config_str:
            reasoning += f"Configuration: {', '.join(config_str)}."
        
        return reasoning
