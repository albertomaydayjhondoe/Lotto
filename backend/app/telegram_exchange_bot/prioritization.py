"""
Prioritization System - Sprint 7B
Sistema de priorización de contenido usando BrainOrchestrator ML.

⚠️ INTEGRACIÓN CON ML ORCHESTRATOR ⚠️
1. Recibe instrucciones de BrainOrchestrator
2. Score de usuarios/grupos según engagement
3. Prioriza contenido según estrategia ML
4. Decide qué apoyar primero basado en ROI
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.telegram_exchange_bot.models import (
    Platform,
    InteractionType,
    PriorityLevel,
    OurContent
)
from app.brain.brain_orchestrator_stub import (
    get_brain_orchestrator,
    BrainOrchestratorStub
)

logger = logging.getLogger(__name__)


class ContentStrategy(str, Enum):
    """Estrategia de contenido."""
    LAUNCH = "launch"  # Lanzamiento nuevo
    MICROMOMENT = "micromoment"  # Microoportunidad detectada
    ROUTINE = "routine"  # Contenido regular
    SATELLITE = "satellite"  # Contenido satélite de apoyo


@dataclass
class ContentPriorityScore:
    """
    Score de prioridad para contenido.
    
    Combina:
    - Estrategia ML (BrainOrchestrator)
    - Estado actual (reciente, trending)
    - ROI esperado
    """
    content_id: str
    platform: Platform
    strategy: ContentStrategy
    
    # Scores (0.0 - 1.0)
    ml_score: float = 0.0  # Score del ML orchestrator
    recency_score: float = 0.0  # Qué tan reciente es
    engagement_score: float = 0.0  # Engagement esperado
    roi_score: float = 0.0  # ROI histórico
    
    # Score final (weighted)
    final_score: float = 0.0
    priority_level: PriorityLevel = PriorityLevel.MEDIUM
    
    # Metadata
    reasoning: List[str] = field(default_factory=list)
    estimated_cost_eur: float = 0.0


@dataclass
class UserExchangeScore:
    """
    Score de usuario para intercambios.
    
    Evalúa:
    - Historial de cumplimiento
    - Engagement previo
    - Ratio reciprocidad
    """
    telegram_user_id: str
    username: Optional[str]
    
    # Métricas
    total_exchanges: int = 0
    completed_exchanges: int = 0
    failed_exchanges: int = 0
    
    # Scores
    reliability_score: float = 0.0  # completed / total
    engagement_score: float = 0.0  # Avg engagement en sus posts
    reciprocity_score: float = 0.0  # Cuánto nos apoya de vuelta
    
    # Score final
    final_score: float = 0.0
    is_trusted: bool = False


class PriorityManager:
    """
    Gestor de prioridades del Telegram Exchange Bot.
    
    Funciones:
    1. Consultar BrainOrchestrator para estrategia ML
    2. Calcular score de contenido propio
    3. Calcular score de usuarios externos
    4. Decidir qué apoyar primero
    5. Queue de ejecución para Executor
    """
    
    def __init__(
        self,
        db: Session,
        brain: Optional[BrainOrchestratorStub] = None
    ):
        """
        Args:
            db: Sesión de BD
            brain: Brain Orchestrator (opcional, usa global si None)
        """
        self.db = db
        self.brain = brain or get_brain_orchestrator()
        
        # Pesos para score final de contenido
        self.content_weights = {
            "ml_score": 0.40,  # ML orchestrator tiene más peso
            "recency_score": 0.25,
            "engagement_score": 0.20,
            "roi_score": 0.15
        }
        
        # Pesos para score de usuarios
        self.user_weights = {
            "reliability_score": 0.50,  # Confiabilidad es crítica
            "engagement_score": 0.30,
            "reciprocity_score": 0.20
        }
        
        logger.info("PriorityManager inicializado")
    
    async def get_ml_strategy(self) -> Dict[str, Any]:
        """
        Consulta BrainOrchestrator para estrategia actual.
        
        Returns:
            Dict con:
                - priority_content: List[str] (IDs contenido prioritario)
                - strategy: str (launch/micromoment/routine)
                - confidence: float
                - reasoning: str
        """
        try:
            # TODO: Implementar consulta real al Brain
            # Por ahora, retornar estrategia mock
            status = self.brain.get_orchestrator_status()
            
            return {
                "priority_content": [],  # STUB
                "strategy": "routine",
                "confidence": 0.75,
                "reasoning": "ML orchestrator in STUB mode",
                "mode": status.get("mode", "stub")
            }
            
        except Exception as e:
            logger.error(f"Error consultando ML strategy: {e}")
            return {
                "priority_content": [],
                "strategy": "routine",
                "confidence": 0.0,
                "reasoning": f"Error: {e}",
                "mode": "error"
            }
    
    async def calculate_content_priority(
        self,
        content: OurContent,
        ml_strategy: Optional[Dict[str, Any]] = None
    ) -> ContentPriorityScore:
        """
        Calcula score de prioridad para contenido propio.
        
        Args:
            content: OurContent a evaluar
            ml_strategy: Estrategia ML (opcional)
            
        Returns:
            ContentPriorityScore
        """
        if not ml_strategy:
            ml_strategy = await self.get_ml_strategy()
        
        score = ContentPriorityScore(
            content_id=content.content_id,
            platform=content.platform,
            strategy=self._determine_strategy(content, ml_strategy)
        )
        
        # 1. ML Score
        priority_content = ml_strategy.get("priority_content", [])
        if content.content_id in priority_content:
            score.ml_score = 0.95
            score.reasoning.append("ML orchestrator marked as priority")
        else:
            score.ml_score = ml_strategy.get("confidence", 0.5)
        
        # 2. Recency Score (más reciente = más score)
        hours_since_published = (datetime.utcnow() - content.published_at).total_seconds() / 3600
        if hours_since_published < 24:
            score.recency_score = 1.0 - (hours_since_published / 24)
            score.reasoning.append(f"Published {hours_since_published:.1f}h ago")
        elif hours_since_published < 72:
            score.recency_score = 0.5
        else:
            score.recency_score = 0.2
        
        # 3. Engagement Score (esperado)
        # TODO: Usar predicción ML si está disponible
        score.engagement_score = 0.7  # Default
        
        # 4. ROI Score (histórico)
        # TODO: Calcular desde metrics.py
        score.roi_score = 0.6  # Default
        
        # 5. Score final (weighted average)
        score.final_score = (
            score.ml_score * self.content_weights["ml_score"] +
            score.recency_score * self.content_weights["recency_score"] +
            score.engagement_score * self.content_weights["engagement_score"] +
            score.roi_score * self.content_weights["roi_score"]
        )
        
        # 6. Determinar priority level
        if score.final_score >= 0.85:
            score.priority_level = PriorityLevel.CRITICAL
        elif score.final_score >= 0.70:
            score.priority_level = PriorityLevel.HIGH
        elif score.final_score >= 0.50:
            score.priority_level = PriorityLevel.MEDIUM
        else:
            score.priority_level = PriorityLevel.LOW
        
        # 7. Estimar costo
        score.estimated_cost_eur = self._estimate_content_cost(content)
        
        return score
    
    async def calculate_user_score(
        self,
        telegram_user_id: str,
        username: Optional[str] = None
    ) -> UserExchangeScore:
        """
        Calcula score de confiabilidad de usuario.
        
        Args:
            telegram_user_id: ID del usuario
            username: Username (opcional)
            
        Returns:
            UserExchangeScore
        """
        score = UserExchangeScore(
            telegram_user_id=telegram_user_id,
            username=username
        )
        
        # TODO: Consultar BD para historial
        # Por ahora, valores mock
        score.total_exchanges = 10
        score.completed_exchanges = 8
        score.failed_exchanges = 2
        
        # 1. Reliability Score
        if score.total_exchanges > 0:
            score.reliability_score = score.completed_exchanges / score.total_exchanges
        else:
            score.reliability_score = 0.5  # Neutral para nuevos usuarios
        
        # 2. Engagement Score
        # TODO: Calcular avg engagement de sus posts
        score.engagement_score = 0.65
        
        # 3. Reciprocity Score
        # TODO: Calcular cuánto nos apoya de vuelta
        score.reciprocity_score = 0.70
        
        # 4. Score final
        score.final_score = (
            score.reliability_score * self.user_weights["reliability_score"] +
            score.engagement_score * self.user_weights["engagement_score"] +
            score.reciprocity_score * self.user_weights["reciprocity_score"]
        )
        
        # 5. Es confiable?
        score.is_trusted = (
            score.reliability_score >= 0.75 and
            score.total_exchanges >= 5
        )
        
        return score
    
    async def prioritize_execution_queue(
        self,
        pending_interactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioriza queue de interacciones pendientes.
        
        Args:
            pending_interactions: Lista de interacciones a ejecutar
            
        Returns:
            Lista ordenada por prioridad (más alta primero)
        """
        ml_strategy = await self.get_ml_strategy()
        
        scored_interactions = []
        
        for interaction in pending_interactions:
            # Score el contenido si es nuestro
            if interaction.get("is_our_content", False):
                content = interaction.get("content")
                if content:
                    priority_score = await self.calculate_content_priority(
                        content=content,
                        ml_strategy=ml_strategy
                    )
                    scored_interactions.append({
                        **interaction,
                        "priority_score": priority_score.final_score,
                        "priority_level": priority_score.priority_level.value
                    })
            else:
                # Score el usuario externo
                user_score = await self.calculate_user_score(
                    telegram_user_id=interaction.get("user_id", ""),
                    username=interaction.get("username")
                )
                
                # Ajustar score según user reliability
                base_priority = interaction.get("priority_score", 0.5)
                adjusted_priority = base_priority * user_score.final_score
                
                scored_interactions.append({
                    **interaction,
                    "priority_score": adjusted_priority,
                    "user_reliability": user_score.reliability_score
                })
        
        # Ordenar por priority_score descendente
        scored_interactions.sort(
            key=lambda x: x.get("priority_score", 0.0),
            reverse=True
        )
        
        return scored_interactions
    
    def _determine_strategy(
        self,
        content: OurContent,
        ml_strategy: Dict[str, Any]
    ) -> ContentStrategy:
        """Determina estrategia de contenido."""
        strategy_name = ml_strategy.get("strategy", "routine")
        
        if strategy_name == "launch":
            return ContentStrategy.LAUNCH
        elif strategy_name == "micromoment":
            return ContentStrategy.MICROMOMENT
        elif strategy_name == "satellite":
            return ContentStrategy.SATELLITE
        else:
            return ContentStrategy.ROUTINE
    
    def _estimate_content_cost(self, content: OurContent) -> float:
        """
        Estima costo de promoción de contenido.
        
        Basado en:
        - Platform (YouTube más caro que Instagram)
        - Tipo de interacción
        - Cantidad de apoyos necesarios
        """
        base_costs = {
            Platform.YOUTUBE: 0.05,  # €0.05 per interaction
            Platform.INSTAGRAM: 0.03,
            Platform.TIKTOK: 0.04
        }
        
        base = base_costs.get(content.platform, 0.04)
        
        # TODO: Calcular basado en target_interactions necesarias
        estimated_interactions = 50  # Mock
        
        return base * estimated_interactions
    
    async def get_priority_recommendations(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retorna recomendaciones de contenido a promocionar.
        
        Args:
            limit: Máximo número de recomendaciones
            
        Returns:
            Lista de contenidos priorizados con reasoning
        """
        ml_strategy = await self.get_ml_strategy()
        
        # TODO: Consultar OurContent de BD
        # Por ahora, retornar mock
        
        recommendations = []
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna stats del priority manager."""
        return {
            "content_weights": self.content_weights,
            "user_weights": self.user_weights,
            "brain_mode": self.brain.get_orchestrator_status().get("mode", "unknown")
        }
