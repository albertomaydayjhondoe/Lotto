"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Identity-Aware Clip Scoring

Sistema de scoring de clips que considera:
- Metadata visual (Vision Engine)
- Metadata de audio (Content Engine)
- Identidad y nicho de la cuenta
- Predicciones de viralidad (ML Persistence)
- Historial de performance
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .sat_intel_contracts import (
    ClipScore,
    ContentMetadata,
    AccountProfile,
    ContentType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class ScoringConfig:
    """Configuración del scoring"""
    
    # Pesos de factores (deben sumar 1.0)
    niche_match_weight: float = 0.25
    virality_weight: float = 0.30
    timing_weight: float = 0.15
    uniqueness_weight: float = 0.20
    audio_match_weight: float = 0.10
    
    # Thresholds
    min_niche_match: float = 0.3
    min_virality: float = 0.2
    
    # Decay para contenido usado
    reuse_decay_factor: float = 0.5
    reuse_lookback_days: int = 30


# ============================================================================
# IDENTITY-AWARE CLIP SCORER
# ============================================================================

class IdentityAwareClipScorer:
    """
    Scorer de clips con conciencia de identidad de cuenta.
    
    Flujo:
    1. Recibe content metadata + account profile
    2. Calcula score de niche match
    3. Calcula score de viralidad (ML)
    4. Calcula score de timing
    5. Calcula score de uniqueness (vs historial)
    6. Calcula score de audio match
    7. Combina scores con pesos → score total
    """
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        logger.info(f"IdentityAwareClipScorer initialized with weights: "
                   f"niche={self.config.niche_match_weight}, "
                   f"virality={self.config.virality_weight}, "
                   f"timing={self.config.timing_weight}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def score_clip(
        self,
        content: ContentMetadata,
        account: AccountProfile,
        current_time: Optional[datetime] = None
    ) -> ClipScore:
        """
        Score un clip para una cuenta específica.
        
        Args:
            content: Metadata del contenido
            account: Perfil de la cuenta
            current_time: Tiempo actual (para timing score)
        
        Returns:
            ClipScore con breakdown detallado
        """
        current_time = current_time or datetime.now()
        
        logger.debug(f"Scoring clip {content.content_id} for account {account.account_id}")
        
        # Calcular scores individuales
        niche_match = self._score_niche_match(content, account)
        virality = self._score_virality(content, account)
        timing = self._score_timing(current_time, account)
        uniqueness = self._score_uniqueness(content, account)
        audio_match = self._score_audio_match(content, account)
        
        # Score total (weighted average)
        total_score = (
            niche_match * self.config.niche_match_weight +
            virality * self.config.virality_weight +
            timing * self.config.timing_weight +
            uniqueness * self.config.uniqueness_weight +
            audio_match * self.config.audio_match_weight
        )
        
        # Aplicar thresholds mínimos
        if niche_match < self.config.min_niche_match:
            total_score *= 0.5  # Penalización por mal match
            logger.debug(f"Low niche match ({niche_match:.2f}), penalizing score")
        
        if virality < self.config.min_virality:
            total_score *= 0.7  # Penalización por baja viralidad esperada
            logger.debug(f"Low virality ({virality:.2f}), penalizing score")
        
        # Calcular confidence
        confidence = self._calculate_confidence(content, account)
        
        # Reasoning
        reasoning = self._generate_reasoning(
            niche_match, virality, timing, uniqueness, audio_match, total_score
        )
        
        return ClipScore(
            content_id=content.content_id,
            account_id=account.account_id,
            total_score=min(total_score, 1.0),
            niche_match_score=niche_match,
            virality_score=virality,
            timing_score=timing,
            uniqueness_score=uniqueness,
            audio_match_score=audio_match,
            confidence=confidence,
            scored_at=current_time,
            reasoning=reasoning
        )
    
    def batch_score_clips(
        self,
        contents: List[ContentMetadata],
        account: AccountProfile,
        current_time: Optional[datetime] = None
    ) -> List[ClipScore]:
        """Score múltiples clips para una cuenta"""
        return [
            self.score_clip(content, account, current_time)
            for content in contents
        ]
    
    def score_matrix(
        self,
        contents: List[ContentMetadata],
        accounts: List[AccountProfile],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, ClipScore]]:
        """
        Score matriz completa: todos los clips para todas las cuentas.
        
        Returns:
            Dict[content_id][account_id] = ClipScore
        """
        matrix = {}
        
        for content in contents:
            matrix[content.content_id] = {}
            for account in accounts:
                score = self.score_clip(content, account, current_time)
                matrix[content.content_id][account.account_id] = score
        
        logger.info(f"Scored matrix: {len(contents)} clips × {len(accounts)} accounts")
        return matrix
    
    # ========================================================================
    # SCORING COMPONENTS
    # ========================================================================
    
    def _score_niche_match(self, content: ContentMetadata, account: AccountProfile) -> float:
        """
        Score de match con el nicho de la cuenta.
        
        Considera:
        - Visual tags match con nicho
        - Scene types apropiados
        - Color palette alignment
        """
        # TODO: Real implementation con Vision Engine metadata
        # Por ahora: simulación basada en tags
        
        niche_keywords = self._get_niche_keywords(account.niche_id)
        
        # Match de visual tags
        tag_matches = sum(1 for tag in content.visual_tags if any(kw in tag.lower() for kw in niche_keywords))
        tag_score = min(tag_matches / max(len(niche_keywords), 1), 1.0) if content.visual_tags else 0.5
        
        # Scene types match
        scene_score = 0.7  # Default
        if content.scene_types:
            preferred_scenes = self._get_preferred_scenes(account.niche_id)
            scene_matches = sum(1 for scene in content.scene_types if scene in preferred_scenes)
            scene_score = min(scene_matches / max(len(preferred_scenes), 1), 1.0)
        
        # Motion intensity check
        motion_score = 1.0 - abs(content.motion_intensity - 0.7)  # Prefer medium-high motion
        
        # Combine
        return (tag_score * 0.5 + scene_score * 0.3 + motion_score * 0.2)
    
    def _score_virality(self, content: ContentMetadata, account: AccountProfile) -> float:
        """
        Score de viralidad predicha.
        
        Considera:
        - Historical performance del contenido (si existe)
        - ML model predictions (TODO: integración con ML Persistence)
        - Características virales (motion, energy, etc.)
        """
        # Si hay data histórica, usarla
        if content.avg_virality_score is not None:
            historical_score = content.avg_virality_score
        else:
            historical_score = 0.5  # Neutral
        
        # TODO: Integrar con ML Persistence para predicciones
        # Por ahora: heurística basada en features
        
        # Energy & motion boost
        energy_boost = content.energy * 0.2
        motion_boost = content.motion_intensity * 0.15
        
        # Duration sweet spot (7-15 segundos)
        if 7 <= content.duration_seconds <= 15:
            duration_score = 1.0
        elif content.duration_seconds < 7:
            duration_score = 0.7
        else:
            duration_score = max(0.5, 1.0 - (content.duration_seconds - 15) * 0.05)
        
        # Combine
        virality = (
            historical_score * 0.5 +
            duration_score * 0.3 +
            energy_boost +
            motion_boost
        )
        
        return min(virality, 1.0)
    
    def _score_timing(self, current_time: datetime, account: AccountProfile) -> float:
        """
        Score de timing basado en optimal hours/days del account.
        
        Si estamos cerca de una ventana óptima → score alto
        Si estamos lejos → score bajo
        """
        current_hour = current_time.hour
        current_weekday = current_time.weekday()
        
        # Score de hora
        if not account.optimal_hours:
            hour_score = 0.7  # Neutral si no hay data
        else:
            # Distancia a la hora óptima más cercana
            min_distance = min(abs(current_hour - h) for h in account.optimal_hours)
            hour_score = max(0.0, 1.0 - (min_distance / 12.0))  # Decay lineal
        
        # Score de día
        if not account.optimal_days:
            day_score = 0.7
        else:
            day_score = 1.0 if current_weekday in account.optimal_days else 0.5
        
        return (hour_score * 0.7 + day_score * 0.3)
    
    def _score_uniqueness(self, content: ContentMetadata, account: AccountProfile) -> float:
        """
        Score de uniqueness: qué tan poco usado es este contenido.
        
        Considera:
        - Si ya fue usado por esta cuenta
        - Cuánto tiempo pasó desde último uso
        - Si el audio ya fue usado
        """
        # Check si el content_id ya fue usado
        if content.content_id in account.recent_content_ids:
            # Aplicar decay
            return self.config.reuse_decay_factor
        
        # Check si el audio ya fue usado
        if content.audio_track_id and content.audio_track_id in account.recent_audio_ids:
            return 0.8  # Leve penalización
        
        # Completamente nuevo
        return 1.0
    
    def _score_audio_match(self, content: ContentMetadata, account: AccountProfile) -> float:
        """
        Score de match del audio con el estilo de la cuenta.
        
        Considera:
        - BPM alignment
        - Energy/valence match con historial
        """
        if not content.audio_track_id:
            return 0.5  # Sin audio = neutral
        
        # TODO: Integrar con Content Engine para audio analysis
        # Por ahora: heurística basada en energy/valence
        
        # Energy sweet spot para cuentas (medium-high)
        energy_score = 1.0 - abs(content.energy - 0.7)
        
        # Valence positivo generalmente mejor
        valence_score = content.valence
        
        # BPM range check (80-140 BPM generalmente bueno para TikTok)
        if content.bpm:
            if 80 <= content.bpm <= 140:
                bpm_score = 1.0
            else:
                bpm_score = 0.6
        else:
            bpm_score = 0.7
        
        return (energy_score * 0.4 + valence_score * 0.3 + bpm_score * 0.3)
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _calculate_confidence(self, content: ContentMetadata, account: AccountProfile) -> float:
        """Calcula confidence del score basado en data disponible"""
        confidence = 0.5  # Base
        
        # Boost si hay data histórica
        if content.avg_virality_score is not None:
            confidence += 0.2
        if content.avg_retention is not None:
            confidence += 0.1
        
        # Boost si la cuenta tiene historial
        if account.total_posts > 10:
            confidence += 0.1
        if account.optimal_hours:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_reasoning(
        self,
        niche: float,
        virality: float,
        timing: float,
        uniqueness: float,
        audio: float,
        total: float
    ) -> str:
        """Genera explicación human-readable del score"""
        parts = []
        
        # Highlight strengths
        if niche >= 0.7:
            parts.append(f"Strong niche match ({niche:.2f})")
        if virality >= 0.7:
            parts.append(f"High virality potential ({virality:.2f})")
        if uniqueness >= 0.9:
            parts.append("Fresh content (unused)")
        
        # Highlight weaknesses
        if niche < 0.4:
            parts.append(f"Weak niche match ({niche:.2f})")
        if virality < 0.3:
            parts.append(f"Low virality prediction ({virality:.2f})")
        if uniqueness < 0.6:
            parts.append("Content already used recently")
        
        # Timing note
        if timing >= 0.8:
            parts.append("Optimal timing window")
        elif timing < 0.5:
            parts.append("Suboptimal timing")
        
        if not parts:
            parts.append("Balanced score across all factors")
        
        return f"Total: {total:.2f} | " + ", ".join(parts)
    
    def _get_niche_keywords(self, niche_id: str) -> List[str]:
        """Get keywords para un nicho (TODO: cargar de DB)"""
        # Simplified mapping
        niche_map = {
            "music": ["music", "song", "beat", "audio", "sound"],
            "dance": ["dance", "movement", "choreography", "rhythm"],
            "comedy": ["funny", "laugh", "humor", "joke"],
            "food": ["food", "cooking", "recipe", "meal"],
            "tech": ["tech", "gadget", "code", "software"],
        }
        return niche_map.get(niche_id, ["general", "content"])
    
    def _get_preferred_scenes(self, niche_id: str) -> List[str]:
        """Get scene types preferidos para un nicho"""
        scene_map = {
            "music": ["studio", "stage", "concert", "closeup"],
            "dance": ["dance_floor", "stage", "outdoor", "group"],
            "comedy": ["indoor", "talking_head", "skit"],
            "food": ["kitchen", "table", "closeup"],
            "tech": ["office", "desk", "screen_recording"],
        }
        return scene_map.get(niche_id, ["general"])


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def score_clip_simple(
    content_id: str,
    account_id: str,
    niche_id: str = "music"
) -> ClipScore:
    """
    Helper para scoring rápido con valores default.
    
    Útil para testing y demos.
    """
    scorer = IdentityAwareClipScorer()
    
    # Mock content
    content = ContentMetadata(
        content_id=content_id,
        content_type=ContentType.VIDEO_CLIP,
        duration_seconds=12.0,
        visual_tags=["music", "performance"],
        energy=0.8,
        valence=0.7,
    )
    
    # Mock account
    account = AccountProfile(
        account_id=account_id,
        niche_id=niche_id,
        niche_name=niche_id.title(),
        is_active=True,
        total_posts=50,
        optimal_hours=[10, 14, 18, 21],
    )
    
    return scorer.score_clip(content, account)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ScoringConfig",
    "IdentityAwareClipScorer",
    "score_clip_simple",
]
