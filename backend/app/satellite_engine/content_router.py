"""
Satellite Content Router - Sprint 8
Vision Engine + ML Virality para routing inteligente de contenido.

Selecciona qué vídeo tiene mayor probabilidad de viralizarse,
qué extractos encajan con letra, qué nichos demandan qué visuales.
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Tipos de contenido."""
    VIDEO_CLIP = "video_clip"
    SCENE_EXTRACT = "scene_extract"
    AI_GENERATED = "ai_generated"
    MIXED_MEDIA = "mixed_media"


class ViralityLevel(Enum):
    """Niveles de viralidad predichos."""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MEDIUM = "medium"          # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%


@dataclass
class ContentCandidate:
    """Candidato de contenido para routing."""
    content_id: str
    content_type: ContentType
    source_path: str
    duration_seconds: float
    
    # Vision Analysis
    visual_tags: List[str] = field(default_factory=list)
    dominant_colors: List[str] = field(default_factory=list)
    scene_description: str = ""
    motion_intensity: float = 0.5  # 0.0 - 1.0
    
    # Audio matching
    music_track_id: Optional[str] = None
    lyric_keywords: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_color_match_score(self, niche_palette: List[str]) -> float:
        """Calcula score de coincidencia de colores con nicho."""
        if not self.dominant_colors or not niche_palette:
            return 0.0
        
        matches = sum(1 for color in self.dominant_colors if color in niche_palette)
        return matches / len(niche_palette)


@dataclass
class ViralityScore:
    """Score de viralidad predicho."""
    overall_score: float  # 0.0 - 1.0
    level: ViralityLevel
    
    # Factores individuales
    visual_appeal: float = 0.5
    niche_fit: float = 0.5
    music_sync: float = 0.5
    timing_optimal: float = 0.5
    trend_alignment: float = 0.5
    
    # Explicación
    reasoning: str = ""
    
    def __post_init__(self):
        """Determina level basado en overall_score."""
        if self.overall_score >= 0.8:
            self.level = ViralityLevel.VERY_HIGH
        elif self.overall_score >= 0.6:
            self.level = ViralityLevel.HIGH
        elif self.overall_score >= 0.4:
            self.level = ViralityLevel.MEDIUM
        elif self.overall_score >= 0.2:
            self.level = ViralityLevel.LOW
        else:
            self.level = ViralityLevel.VERY_LOW


@dataclass
class RoutingDecision:
    """Decisión de routing de contenido."""
    account_id: str
    content_candidate: ContentCandidate
    virality_score: ViralityScore
    niche_match_score: float
    recommended_platform: str  # "tiktok", "instagram", "youtube"
    recommended_time: Optional[datetime] = None
    priority: int = 5  # 1-10, 10 = highest
    reasoning: str = ""


class VisionEngine:
    """
    Motor de análisis visual simplificado.
    
    En producción, integraría con:
    - OpenAI Vision API
    - Google Cloud Vision
    - Custom ML models
    """
    
    def analyze_content(self, content_path: str) -> Dict[str, any]:
        """
        Analiza contenido visual (simulado).
        
        En producción, usaría APIs reales de vision.
        """
        # Simulación de análisis visual
        # TODO Sprint 8+: Integrar con OpenAI Vision o Google Cloud Vision
        
        return {
            "visual_tags": self._detect_tags(content_path),
            "dominant_colors": self._extract_colors(content_path),
            "scene_description": self._describe_scene(content_path),
            "motion_intensity": random.uniform(0.3, 0.9),
            "quality_score": random.uniform(0.6, 1.0)
        }
    
    def _detect_tags(self, content_path: str) -> List[str]:
        """Detecta tags visuales (simulado)."""
        # En producción: Vision API
        tag_pool = [
            "urban", "dark", "cinematic", "moody", "neon",
            "action", "drama", "aesthetic", "vintage", "modern",
            "night", "city", "character", "close_up", "wide_shot"
        ]
        return random.sample(tag_pool, k=random.randint(3, 6))
    
    def _extract_colors(self, content_path: str) -> List[str]:
        """Extrae colores dominantes (simulado)."""
        # En producción: Color extraction
        color_pool = [
            "#1a1a2e", "#16213e", "#0f3460", "#e94560",
            "#ff0000", "#000000", "#1a1a1a", "#ff6b6b",
            "#ff6b00", "#1e90ff", "#ffd700", "#9d00ff"
        ]
        return random.sample(color_pool, k=random.randint(2, 4))
    
    def _describe_scene(self, content_path: str) -> str:
        """Describe escena (simulado)."""
        # En producción: GPT-4 Vision
        descriptions = [
            "Dark urban scene with dramatic lighting",
            "Character in moody cinematic setting",
            "Fast-paced action sequence with motion blur",
            "Aesthetic night cityscape with neon lights",
            "Close-up character shot with emotional intensity"
        ]
        return random.choice(descriptions)


class MLViralityPredictor:
    """
    Predictor ML de viralidad.
    
    En producción, entrenaría con datos históricos:
    - Views, likes, shares, comments
    - Retention rate
    - CTR
    - Platform-specific metrics
    """
    
    def __init__(self):
        self.historical_data: List[Dict] = []
    
    def predict_virality(
        self,
        content: ContentCandidate,
        niche_name: str,
        platform: str,
        current_time: datetime
    ) -> ViralityScore:
        """
        Predice viralidad de contenido.
        
        En producción, usaría:
        - XGBoost / LightGBM entrenados
        - Features: tags, colores, motion, timing, platform, niche
        - Labels: virality_score (0-1) from historical performance
        """
        # Simulación de ML prediction
        # TODO Sprint 8+: Entrenar modelo real con datos históricos
        
        # Factors
        visual_appeal = random.uniform(0.5, 0.95)
        niche_fit = random.uniform(0.6, 1.0)
        music_sync = random.uniform(0.7, 1.0)
        timing_optimal = self._calculate_timing_score(current_time)
        trend_alignment = random.uniform(0.4, 0.9)
        
        # Weighted average
        overall = (
            visual_appeal * 0.25 +
            niche_fit * 0.25 +
            music_sync * 0.20 +
            timing_optimal * 0.15 +
            trend_alignment * 0.15
        )
        
        reasoning = f"Visual={visual_appeal:.2f}, Niche={niche_fit:.2f}, Music={music_sync:.2f}, Timing={timing_optimal:.2f}"
        
        return ViralityScore(
            overall_score=overall,
            level=ViralityLevel.HIGH,  # Se determina en __post_init__
            visual_appeal=visual_appeal,
            niche_fit=niche_fit,
            music_sync=music_sync,
            timing_optimal=timing_optimal,
            trend_alignment=trend_alignment,
            reasoning=reasoning
        )
    
    def _calculate_timing_score(self, current_time: datetime) -> float:
        """Calcula score de timing óptimo."""
        hour = current_time.hour
        
        # Prime hours: 18-23 = high score
        if 18 <= hour <= 23:
            return random.uniform(0.8, 1.0)
        # Good hours: 12-17 or 6-11
        elif (12 <= hour <= 17) or (6 <= hour <= 11):
            return random.uniform(0.6, 0.8)
        # Off-peak: 0-5
        else:
            return random.uniform(0.3, 0.6)
    
    def record_performance(
        self,
        content_id: str,
        virality_score: float,
        actual_views: int,
        actual_engagement: float
    ):
        """Registra performance real para reentrenamiento futuro."""
        self.historical_data.append({
            "content_id": content_id,
            "predicted_virality": virality_score,
            "actual_views": actual_views,
            "actual_engagement": actual_engagement,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Recorded performance: {content_id} -> {actual_views} views")


class SatelliteContentRouter:
    """
    Router inteligente de contenido para cuentas satélite.
    
    Features:
    - Vision analysis de contenido
    - ML virality prediction
    - Niche matching
    - Platform optimization
    - Timing optimization
    """
    
    def __init__(self):
        self.vision_engine = VisionEngine()
        self.ml_predictor = MLViralityPredictor()
        self.content_cache: Dict[str, ContentCandidate] = {}
        
        logger.info("SatelliteContentRouter initialized")
    
    def analyze_content(
        self,
        content_id: str,
        content_type: ContentType,
        source_path: str,
        duration_seconds: float,
        music_track_id: Optional[str] = None,
        lyric_keywords: Optional[List[str]] = None
    ) -> ContentCandidate:
        """
        Analiza contenido con Vision Engine.
        
        Args:
            content_id: ID único del contenido
            content_type: Tipo de contenido
            source_path: Path al archivo
            duration_seconds: Duración
            music_track_id: ID de track de música
            lyric_keywords: Keywords de lyrics
            
        Returns:
            ContentCandidate con análisis visual
        """
        # Vision analysis
        vision_data = self.vision_engine.analyze_content(source_path)
        
        candidate = ContentCandidate(
            content_id=content_id,
            content_type=content_type,
            source_path=source_path,
            duration_seconds=duration_seconds,
            visual_tags=vision_data["visual_tags"],
            dominant_colors=vision_data["dominant_colors"],
            scene_description=vision_data["scene_description"],
            motion_intensity=vision_data["motion_intensity"],
            music_track_id=music_track_id,
            lyric_keywords=lyric_keywords or []
        )
        
        # Cache
        self.content_cache[content_id] = candidate
        
        logger.info(f"Analyzed content: {content_id} -> {len(vision_data['visual_tags'])} tags")
        return candidate
    
    def route_content_to_account(
        self,
        account_id: str,
        niche_name: str,
        niche_palette: List[str],
        content_candidates: List[ContentCandidate],
        preferred_platform: str = "tiktok",
        target_time: Optional[datetime] = None
    ) -> RoutingDecision:
        """
        Selecciona mejor contenido para cuenta.
        
        Args:
            account_id: ID de cuenta satélite
            niche_name: Nombre del nicho
            niche_palette: Paleta de colores del nicho
            content_candidates: Lista de candidatos
            preferred_platform: Plataforma preferida
            target_time: Tiempo objetivo de publicación
            
        Returns:
            RoutingDecision con mejor contenido
        """
        if not content_candidates:
            raise ValueError("No content candidates provided")
        
        current_time = target_time or datetime.now()
        
        # Score all candidates
        scored_candidates: List[Tuple[ContentCandidate, ViralityScore, float]] = []
        
        for candidate in content_candidates:
            # Predict virality
            virality_score = self.ml_predictor.predict_virality(
                candidate,
                niche_name,
                preferred_platform,
                current_time
            )
            
            # Niche match score (color matching)
            niche_match = candidate.get_color_match_score(niche_palette)
            
            scored_candidates.append((candidate, virality_score, niche_match))
        
        # Sort by combined score
        scored_candidates.sort(
            key=lambda x: (x[1].overall_score * 0.7 + x[2] * 0.3),
            reverse=True
        )
        
        # Best candidate
        best_content, best_virality, best_niche_match = scored_candidates[0]
        
        # Determine priority
        priority = self._calculate_priority(best_virality.overall_score)
        
        decision = RoutingDecision(
            account_id=account_id,
            content_candidate=best_content,
            virality_score=best_virality,
            niche_match_score=best_niche_match,
            recommended_platform=preferred_platform,
            recommended_time=current_time,
            priority=priority,
            reasoning=f"Best virality: {best_virality.level.value}, Niche match: {best_niche_match:.2f}"
        )
        
        logger.info(f"Routed content: {account_id} -> {best_content.content_id} (score={best_virality.overall_score:.2f})")
        return decision
    
    def _calculate_priority(self, virality_score: float) -> int:
        """Calcula prioridad basada en virality score."""
        if virality_score >= 0.8:
            return 10
        elif virality_score >= 0.6:
            return 8
        elif virality_score >= 0.4:
            return 6
        elif virality_score >= 0.2:
            return 4
        else:
            return 2
    
    def batch_route_content(
        self,
        accounts: List[Dict[str, any]],
        content_pool: List[ContentCandidate]
    ) -> List[RoutingDecision]:
        """
        Routing batch para múltiples cuentas.
        
        Args:
            accounts: Lista de dicts con account_id, niche_name, niche_palette, platform
            content_pool: Pool de contenidos disponibles
            
        Returns:
            Lista de RoutingDecisions
        """
        decisions = []
        
        for account in accounts:
            try:
                decision = self.route_content_to_account(
                    account_id=account["account_id"],
                    niche_name=account["niche_name"],
                    niche_palette=account.get("niche_palette", []),
                    content_candidates=content_pool,
                    preferred_platform=account.get("platform", "tiktok")
                )
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Failed to route for {account['account_id']}: {e}")
        
        logger.info(f"Batch routed: {len(decisions)} accounts")
        return decisions
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del router."""
        return {
            "cached_content": len(self.content_cache),
            "historical_records": len(self.ml_predictor.historical_data)
        }
