"""
SPRINT 12.1 - Human-Assisted Warm-Up Scheduler
Module: Warmup Task Generator

Diseña acciones humanas adaptadas según:
- Estado (W1-3, W4-7, W8-14)
- Plataforma (TikTok, Instagram, YouTube Shorts)
- Perfil narrativo (ProfileObject)
- Métricas actuales
- Señales de riesgo
- Comportamiento previo
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .account_models import AccountState, PlatformType, AccountWarmupMetrics, AccountRiskProfile
from .human_warmup_scheduler import HumanWarmupAction

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class WarmupTaskGeneratorConfig:
    """Configuración del generador de tareas"""
    
    # Adaptive thresholds
    high_risk_reduce_actions: float = 0.5  # 50% reduction if risk > 0.5
    low_engagement_increase_scroll: float = 1.3  # 30% more scroll if low engagement
    
    # Platform-specific adjustments
    tiktok_scroll_multiplier: float = 1.0
    instagram_scroll_multiplier: float = 1.2  # IG needs more browsing
    youtube_shorts_scroll_multiplier: float = 0.9
    
    # Profile-based adjustments
    low_automation_conservative: float = 0.8  # Reduce actions for low automation accounts
    high_risk_tolerance_boost: float = 1.1  # Slightly more for high risk tolerance
    
    # Behavioral adaptation
    consecutive_failures_reduce: int = 2  # After N failures, reduce complexity
    success_streak_increase: int = 3  # After N successes, can increase slightly


# ============================================================================
# WARMUP TASK GENERATOR
# ============================================================================

class WarmupTaskGenerator:
    """
    Generador avanzado de tareas de warmup.
    
    Responsabilidades:
    - Adaptar acciones según contexto completo
    - Ajustar por señales de riesgo
    - Personalizar por plataforma
    - Respetar perfil narrativo
    - Considerar historial
    """
    
    def __init__(self, config: Optional[WarmupTaskGeneratorConfig] = None):
        self.config = config or WarmupTaskGeneratorConfig()
        
        # History tracking
        self._action_history: Dict[str, List[Dict]] = {}  # account_id -> [actions]
        
        logger.info("WarmupTaskGenerator initialized")
    
    # ========================================================================
    # PUBLIC API - ADAPTIVE GENERATION
    # ========================================================================
    
    def generate_adaptive_actions(
        self,
        account_id: str,
        warmup_phase: AccountState,
        platform: PlatformType,
        profile: Optional[Dict] = None,
        metrics: Optional[AccountWarmupMetrics] = None,
        risk_profile: Optional[AccountRiskProfile] = None,
        previous_task_success: Optional[bool] = None
    ) -> List[HumanWarmupAction]:
        """
        Genera acciones adaptadas al contexto completo.
        
        Args:
            account_id: ID de la cuenta
            warmup_phase: Estado actual
            platform: Plataforma
            profile: Perfil narrativo (ProfileObject dict)
            metrics: Métricas actuales
            risk_profile: Perfil de riesgo
            previous_task_success: Si la tarea anterior fue exitosa
        
        Returns:
            Lista de HumanWarmupAction personalizadas
        """
        # Base actions
        actions = self._get_base_actions(warmup_phase)
        
        # Apply platform adjustments
        actions = self._adjust_for_platform(actions, platform)
        
        # Apply profile adjustments
        if profile:
            actions = self._adjust_for_profile(actions, profile)
        
        # Apply risk adjustments
        if risk_profile:
            actions = self._adjust_for_risk(actions, risk_profile)
        
        # Apply metrics adjustments
        if metrics:
            actions = self._adjust_for_metrics(actions, metrics)
        
        # Apply behavioral adaptation
        if previous_task_success is not None:
            actions = self._adjust_for_history(actions, account_id, previous_task_success)
        
        # Record generated actions
        self._record_generation(account_id, actions)
        
        logger.info(f"Generated {len(actions)} adaptive actions for {account_id}")
        
        return actions
    
    def get_platform_recommendations(self, platform: PlatformType) -> Dict:
        """
        Retorna recomendaciones específicas por plataforma.
        """
        recommendations = {
            PlatformType.TIKTOK: {
                "focus": "short_engagement",
                "scroll_speed": "fast",
                "like_ratio": "high",
                "comment_style": "emoji_heavy",
                "optimal_duration": "3-5 min",
                "tips": [
                    "Watch full videos before liking",
                    "Engage with trending sounds",
                    "Use native emojis in comments"
                ]
            },
            PlatformType.INSTAGRAM: {
                "focus": "visual_browsing",
                "scroll_speed": "medium",
                "like_ratio": "medium",
                "comment_style": "thoughtful",
                "optimal_duration": "5-8 min",
                "tips": [
                    "Spend time on stories",
                    "Interact with reels and posts",
                    "Leave meaningful comments"
                ]
            },
            PlatformType.YOUTUBE_SHORTS: {
                "focus": "watch_time",
                "scroll_speed": "slow",
                "like_ratio": "low",
                "comment_style": "detailed",
                "optimal_duration": "4-7 min",
                "tips": [
                    "Watch shorts completely",
                    "Subscribe to relevant channels",
                    "Engage with longer content occasionally"
                ]
            }
        }
        
        return recommendations.get(platform, {})
    
    def suggest_timing(
        self,
        account_id: str,
        profile: Optional[Dict] = None
    ) -> Tuple[int, int]:
        """
        Sugiere ventana horaria óptima.
        
        Returns:
            (start_hour, end_hour)
        """
        if profile and "preferred_hours" in profile:
            hours = profile["preferred_hours"]
            if hours:
                return min(hours), max(hours)
        
        # Default: afternoon/evening (most active)
        return (14, 21)
    
    def get_action_diversity_score(self, account_id: str) -> float:
        """
        Calcula diversidad de acciones históricas.
        
        Returns:
            Score 0.0-1.0 (higher = more diverse)
        """
        history = self._action_history.get(account_id, [])
        if not history:
            return 0.5  # Default
        
        # Count unique action types
        action_types = set()
        for record in history:
            for action in record.get("actions", []):
                action_types.add(action.action_type)
        
        # Normalize (max 5 types: scroll, like, comment, follow, post)
        diversity = len(action_types) / 5.0
        
        return min(1.0, diversity)
    
    # ========================================================================
    # INTERNAL - BASE ACTIONS
    # ========================================================================
    
    def _get_base_actions(self, phase: AccountState) -> List[HumanWarmupAction]:
        """Acciones base por fase"""
        
        actions = []
        
        if phase == AccountState.W1_3:
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=random.randint(180, 360),
                style="casual"
            ))
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=random.randint(2, 4),
                interval_seconds=(20, 90),
                style="natural"
            ))
            if random.random() < 0.3:
                actions.append(HumanWarmupAction(
                    action_type="comment",
                    quantity=1,
                    style="natural"
                ))
        
        elif phase == AccountState.W4_7:
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=random.randint(240, 480),
                style="deliberate"
            ))
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=random.randint(3, 6),
                interval_seconds=(20, 90),
                style="natural"
            ))
            actions.append(HumanWarmupAction(
                action_type="comment",
                quantity=random.randint(1, 2),
                style="natural"
            ))
            if random.random() < 0.4:
                actions.append(HumanWarmupAction(
                    action_type="follow",
                    quantity=1,
                    style="natural"
                ))
        
        elif phase == AccountState.W8_14:
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=random.randint(300, 600),
                style="engaged"
            ))
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=random.randint(4, 8),
                interval_seconds=(20, 90),
                style="natural"
            ))
            actions.append(HumanWarmupAction(
                action_type="comment",
                quantity=random.randint(1, 3),
                style="natural"
            ))
            actions.append(HumanWarmupAction(
                action_type="follow",
                quantity=random.randint(1, 2),
                style="natural"
            ))
            if random.random() < 0.3:
                actions.append(HumanWarmupAction(
                    action_type="post",
                    quantity=1,
                    style="natural"
                ))
        
        return actions
    
    # ========================================================================
    # INTERNAL - ADJUSTMENTS
    # ========================================================================
    
    def _adjust_for_platform(
        self,
        actions: List[HumanWarmupAction],
        platform: PlatformType
    ) -> List[HumanWarmupAction]:
        """Ajusta acciones por plataforma"""
        
        multiplier = 1.0
        if platform == PlatformType.INSTAGRAM:
            multiplier = self.config.instagram_scroll_multiplier
        elif platform == PlatformType.YOUTUBE_SHORTS:
            multiplier = self.config.youtube_shorts_scroll_multiplier
        
        # Adjust scroll durations
        for action in actions:
            if action.action_type == "scroll" and action.duration_seconds:
                action.duration_seconds = int(action.duration_seconds * multiplier)
        
        return actions
    
    def _adjust_for_profile(
        self,
        actions: List[HumanWarmupAction],
        profile: Dict
    ) -> List[HumanWarmupAction]:
        """Ajusta acciones por perfil narrativo"""
        
        # Adjust for automation_level
        automation_level = profile.get("automation_level", 0.5)
        if automation_level < 0.4:  # Low automation = more conservative
            for action in actions:
                if action.quantity:
                    action.quantity = max(1, int(action.quantity * self.config.low_automation_conservative))
        
        # Adjust for risk_tolerance
        risk_tolerance = profile.get("risk_tolerance", 0.5)
        if risk_tolerance > 0.7:  # High risk tolerance = slightly more aggressive
            for action in actions:
                if action.quantity:
                    action.quantity = int(action.quantity * self.config.high_risk_tolerance_boost)
        
        return actions
    
    def _adjust_for_risk(
        self,
        actions: List[HumanWarmupAction],
        risk_profile: AccountRiskProfile
    ) -> List[HumanWarmupAction]:
        """Ajusta acciones por nivel de riesgo"""
        
        if risk_profile.total_risk_score > 0.5:
            # High risk = reduce actions
            for action in actions:
                if action.quantity:
                    action.quantity = max(1, int(action.quantity * self.config.high_risk_reduce_actions))
                if action.duration_seconds:
                    action.duration_seconds = int(action.duration_seconds * self.config.high_risk_reduce_actions)
        
        return actions
    
    def _adjust_for_metrics(
        self,
        actions: List[HumanWarmupAction],
        metrics: AccountWarmupMetrics
    ) -> List[HumanWarmupAction]:
        """Ajusta acciones por métricas actuales"""
        
        # Low engagement = more scroll time
        if metrics.impressions_received > 0:
            engagement_rate = (metrics.likes_received + metrics.comments_received) / metrics.impressions_received
            if engagement_rate < 0.01:  # < 1%
                for action in actions:
                    if action.action_type == "scroll" and action.duration_seconds:
                        action.duration_seconds = int(action.duration_seconds * self.config.low_engagement_increase_scroll)
        
        return actions
    
    def _adjust_for_history(
        self,
        actions: List[HumanWarmupAction],
        account_id: str,
        previous_success: bool
    ) -> List[HumanWarmupAction]:
        """Ajusta acciones por historial comportamental"""
        
        history = self._action_history.get(account_id, [])
        
        # Count recent successes/failures
        recent = history[-5:] if len(history) >= 5 else history
        failures = sum(1 for r in recent if not r.get("success", True))
        
        if failures >= self.config.consecutive_failures_reduce:
            # Reduce complexity after failures
            for action in actions:
                if action.quantity:
                    action.quantity = max(1, action.quantity - 1)
        
        return actions
    
    def _record_generation(self, account_id: str, actions: List[HumanWarmupAction]):
        """Registra generación de acciones"""
        if account_id not in self._action_history:
            self._action_history[account_id] = []
        
        self._action_history[account_id].append({
            "timestamp": datetime.now(),
            "actions": actions,
            "count": len(actions)
        })


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "WarmupTaskGeneratorConfig",
    "WarmupTaskGenerator",
]
