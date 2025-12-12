"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Warmup Policy Engine

Motor de warmup con comportamiento humano y no determinista.
Implementa gaussian jitter, micro-breaks y progresión adaptativa.
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .account_models import AccountState, ActionType

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class WarmupPolicyConfig:
    """Configuración del motor de warmup"""
    
    # Warmup windows (days)
    w1_3_days: Tuple[int, int] = (1, 3)
    w4_7_days: Tuple[int, int] = (4, 7)
    w8_14_days: Tuple[int, int] = (8, 14)
    
    # Gaussian jitter params (mean, std)
    timing_jitter_seconds: Tuple[float, float] = (300.0, 120.0)  # 5min ± 2min
    action_jitter_seconds: Tuple[float, float] = (60.0, 20.0)    # 1min ± 20s
    
    # Micro-breaks
    enable_micro_breaks: bool = True
    micro_break_probability: float = 0.15  # 15% chance per action
    micro_break_duration_seconds: Tuple[float, float] = (120.0, 60.0)  # 2min ± 1min
    
    # Long breaks (human behavior)
    enable_long_breaks: bool = True
    long_break_after_actions: int = 10  # Every ~10 actions
    long_break_duration_seconds: Tuple[float, float] = (1800.0, 600.0)  # 30min ± 10min
    
    # Sleep hours (no activity)
    sleep_hours_start: int = 23  # 11 PM
    sleep_hours_end: int = 7     # 7 AM
    
    # Progression thresholds
    min_actions_before_advance: int = 20
    min_success_rate: float = 0.85


# ============================================================================
# WARMUP ACTION SCHEDULES
# ============================================================================

@dataclass
class WarmupActionSchedule:
    """Schedule de acciones para una fase de warmup"""
    
    phase: AccountState
    day_range: Tuple[int, int]
    
    # Actions per day (mean, std)
    views_per_day: Tuple[int, int] = (0, 0)
    likes_per_day: Tuple[int, int] = (0, 0)
    comments_per_day: Tuple[int, int] = (0, 0)
    follows_per_day: Tuple[int, int] = (0, 0)
    posts_per_day: Tuple[int, int] = (0, 0)
    
    # Recommendations
    recommended_actions: List[ActionType] = None
    avoid_actions: List[ActionType] = None
    
    def __post_init__(self):
        if self.recommended_actions is None:
            self.recommended_actions = []
        if self.avoid_actions is None:
            self.avoid_actions = []


# Default warmup schedules
WARMUP_SCHEDULES = {
    AccountState.W1_3: WarmupActionSchedule(
        phase=AccountState.W1_3,
        day_range=(1, 3),
        views_per_day=(15, 5),      # 15 ± 5 views
        likes_per_day=(1, 1),        # 1-2 likes
        comments_per_day=(0, 0),     # No comments yet
        follows_per_day=(0, 0),      # No follows yet
        posts_per_day=(0, 0),        # No posts yet
        recommended_actions=[ActionType.VIEW, ActionType.LIKE],
        avoid_actions=[ActionType.COMMENT, ActionType.FOLLOW, ActionType.POST, ActionType.SHARE, ActionType.SAVE]
    ),
    
    AccountState.W4_7: WarmupActionSchedule(
        phase=AccountState.W4_7,
        day_range=(4, 7),
        views_per_day=(30, 10),      # 30 ± 10 views
        likes_per_day=(3, 1),        # 2-4 likes
        comments_per_day=(1, 0),     # 0-1 comment (occasional)
        follows_per_day=(1, 0),      # 0-1 follow
        posts_per_day=(0, 0),        # No posts yet
        recommended_actions=[ActionType.VIEW, ActionType.LIKE, ActionType.COMMENT, ActionType.FOLLOW],
        avoid_actions=[ActionType.POST, ActionType.SHARE, ActionType.SAVE]
    ),
    
    AccountState.W8_14: WarmupActionSchedule(
        phase=AccountState.W8_14,
        day_range=(8, 14),
        views_per_day=(50, 15),      # 50 ± 15 views
        likes_per_day=(5, 2),        # 3-7 likes
        comments_per_day=(2, 1),     # 1-3 comments
        follows_per_day=(2, 1),      # 1-3 follows
        posts_per_day=(1, 0),        # 0-1 post (occasional)
        recommended_actions=[ActionType.VIEW, ActionType.LIKE, ActionType.COMMENT, ActionType.FOLLOW, ActionType.POST],
        avoid_actions=[ActionType.SHARE, ActionType.SAVE]
    ),
}


# ============================================================================
# WARMUP POLICY ENGINE
# ============================================================================

class WarmupPolicyEngine:
    """
    Motor de warmup con comportamiento humano.
    
    Responsabilidades:
    - Generar schedules con gaussian jitter
    - Introducir micro-breaks aleatorios
    - Respetar horarios de sueño
    - Adaptar basado en feedback (shadowban, engagement)
    - Validar progresión antes de avanzar
    """
    
    def __init__(self, config: Optional[WarmupPolicyConfig] = None):
        self.config = config or WarmupPolicyConfig()
        
        # Action counters (account_id -> action_type -> count)
        self._action_counters: Dict[str, Dict[ActionType, int]] = {}
        
        # Last action timestamps (account_id -> timestamp)
        self._last_action_times: Dict[str, datetime] = {}
        
        logger.info("WarmupPolicyEngine initialized")
    
    # ========================================================================
    # PUBLIC API - ACTION SCHEDULING
    # ========================================================================
    
    def get_next_action_time(
        self,
        account_id: str,
        action_type: ActionType,
        warmup_phase: AccountState
    ) -> datetime:
        """
        Calcula cuándo debe ejecutarse la próxima acción.
        
        Aplica:
        - Gaussian jitter
        - Micro-breaks aleatorios
        - Long breaks cada N acciones
        - Respeta horarios de sueño
        
        Returns:
            datetime de la próxima acción
        """
        now = datetime.now()
        
        # Get last action time
        last_action = self._last_action_times.get(account_id, now)
        
        # Base delay with gaussian jitter
        mean_delay, std_delay = self.config.timing_jitter_seconds
        delay_seconds = max(0, random.gauss(mean_delay, std_delay))
        
        next_time = last_action + timedelta(seconds=delay_seconds)
        
        # Add micro-break?
        if self.config.enable_micro_breaks:
            if random.random() < self.config.micro_break_probability:
                break_mean, break_std = self.config.micro_break_duration_seconds
                break_duration = max(0, random.gauss(break_mean, break_std))
                next_time += timedelta(seconds=break_duration)
                logger.debug(f"Micro-break added: {break_duration:.0f}s")
        
        # Add long break?
        if self.config.enable_long_breaks:
            total_actions = self._get_total_actions(account_id)
            if total_actions > 0 and total_actions % self.config.long_break_after_actions == 0:
                break_mean, break_std = self.config.long_break_duration_seconds
                break_duration = max(0, random.gauss(break_mean, break_std))
                next_time += timedelta(seconds=break_duration)
                logger.info(f"Long break added: {break_duration/60:.1f}min")
        
        # Skip sleep hours
        next_time = self._skip_sleep_hours(next_time)
        
        return next_time
    
    def can_execute_action(
        self,
        account_id: str,
        action_type: ActionType,
        warmup_phase: AccountState
    ) -> Tuple[bool, str]:
        """
        Valida si una acción puede ejecutarse ahora.
        
        Checks:
        - Acción recomendada para esta fase
        - No excede límite diario
        - Horario válido (no sleep hours)
        
        Returns:
            (can_execute, reason)
        """
        # Get schedule for phase
        schedule = WARMUP_SCHEDULES.get(warmup_phase)
        if not schedule:
            return False, f"No schedule for phase {warmup_phase.value}"
        
        # Check if action is recommended
        if action_type in schedule.avoid_actions:
            return False, f"Action {action_type.value} not recommended for {warmup_phase.value}"
        
        # Check daily limit
        daily_count = self._get_daily_action_count(account_id, action_type)
        daily_limit = self._get_daily_limit(schedule, action_type)
        
        if daily_count >= daily_limit:
            return False, f"Daily limit reached: {daily_count}/{daily_limit}"
        
        # Check sleep hours
        if self._is_sleep_hour(datetime.now()):
            return False, "Sleep hours"
        
        return True, "OK"
    
    def record_action(
        self,
        account_id: str,
        action_type: ActionType,
        success: bool = True
    ):
        """
        Registra una acción ejecutada.
        
        Actualiza contadores y timestamps.
        """
        # Initialize counters if needed
        if account_id not in self._action_counters:
            self._action_counters[account_id] = {}
        
        # Increment counter
        self._action_counters[account_id][action_type] = \
            self._action_counters[account_id].get(action_type, 0) + 1
        
        # Update last action time
        self._last_action_times[account_id] = datetime.now()
        
        logger.debug(f"Recorded action: {account_id} {action_type.value} {'✓' if success else '✗'}")
    
    def get_recommended_actions(
        self,
        warmup_phase: AccountState
    ) -> List[ActionType]:
        """
        Retorna las acciones recomendadas para una fase.
        """
        schedule = WARMUP_SCHEDULES.get(warmup_phase)
        if not schedule:
            return []
        
        return schedule.recommended_actions
    
    def can_advance_to_next_phase(
        self,
        account_id: str,
        current_phase: AccountState,
        days_in_phase: int
    ) -> Tuple[bool, str]:
        """
        Valida si la cuenta está lista para avanzar de fase.
        
        Checks:
        - Tiempo mínimo en fase
        - Número mínimo de acciones
        - Tasa de éxito aceptable
        
        Returns:
            (can_advance, reason)
        """
        schedule = WARMUP_SCHEDULES.get(current_phase)
        if not schedule:
            return True, "No schedule defined"
        
        # Check minimum days
        min_days = schedule.day_range[0]
        if days_in_phase < min_days:
            return False, f"Need {min_days} days in phase (current: {days_in_phase})"
        
        # Check minimum actions
        total_actions = self._get_total_actions(account_id)
        if total_actions < self.config.min_actions_before_advance:
            return False, f"Need {self.config.min_actions_before_advance} actions (current: {total_actions})"
        
        # TODO: Check success rate (requires success/failure tracking)
        
        return True, "Ready to advance"
    
    # ========================================================================
    # PUBLIC API - DAILY PLANNING
    # ========================================================================
    
    def generate_daily_plan(
        self,
        account_id: str,
        warmup_phase: AccountState
    ) -> Dict[ActionType, List[datetime]]:
        """
        Genera un plan diario de acciones con timestamps.
        
        Returns:
            {action_type: [timestamp1, timestamp2, ...]}
        """
        schedule = WARMUP_SCHEDULES.get(warmup_phase)
        if not schedule:
            return {}
        
        plan: Dict[ActionType, List[datetime]] = {}
        
        now = datetime.now()
        current_time = now.replace(hour=8, minute=0, second=0, microsecond=0)  # Start at 8 AM
        
        # Generate actions for each type
        for action_type in schedule.recommended_actions:
            # Get target count with gaussian
            target_count = self._sample_action_count(schedule, action_type)
            
            timestamps = []
            for _ in range(target_count):
                # Calculate next time
                next_time = self.get_next_action_time(account_id, action_type, warmup_phase)
                
                # Ensure within day
                if next_time.date() == now.date():
                    timestamps.append(next_time)
                    current_time = next_time
            
            if timestamps:
                plan[action_type] = sorted(timestamps)
        
        return plan
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _get_total_actions(self, account_id: str) -> int:
        """Total de acciones registradas"""
        if account_id not in self._action_counters:
            return 0
        
        return sum(self._action_counters[account_id].values())
    
    def _get_daily_action_count(self, account_id: str, action_type: ActionType) -> int:
        """Conteo de acciones de hoy (TODO: implement daily reset)"""
        if account_id not in self._action_counters:
            return 0
        
        return self._action_counters[account_id].get(action_type, 0)
    
    def _get_daily_limit(self, schedule: WarmupActionSchedule, action_type: ActionType) -> int:
        """Get daily limit for action type"""
        limits = {
            ActionType.VIEW: schedule.views_per_day[0] + schedule.views_per_day[1],
            ActionType.LIKE: schedule.likes_per_day[0] + schedule.likes_per_day[1],
            ActionType.COMMENT: schedule.comments_per_day[0] + schedule.comments_per_day[1],
            ActionType.FOLLOW: schedule.follows_per_day[0] + schedule.follows_per_day[1],
            ActionType.POST: schedule.posts_per_day[0] + schedule.posts_per_day[1],
            ActionType.SHARE: 0,
            ActionType.SAVE: 0,
        }
        
        return limits.get(action_type, 0)
    
    def _sample_action_count(self, schedule: WarmupActionSchedule, action_type: ActionType) -> int:
        """Sample action count with gaussian"""
        counts = {
            ActionType.VIEW: schedule.views_per_day,
            ActionType.LIKE: schedule.likes_per_day,
            ActionType.COMMENT: schedule.comments_per_day,
            ActionType.FOLLOW: schedule.follows_per_day,
            ActionType.POST: schedule.posts_per_day,
            ActionType.SHARE: (0, 0),
            ActionType.SAVE: (0, 0),
        }
        
        mean, std = counts.get(action_type, (0, 0))
        if std == 0:
            return mean
        
        return max(0, int(random.gauss(mean, std)))
    
    def _is_sleep_hour(self, dt: datetime) -> bool:
        """Check if time is within sleep hours"""
        hour = dt.hour
        
        if self.config.sleep_hours_start > self.config.sleep_hours_end:
            # Wraps midnight (e.g., 23-7)
            return hour >= self.config.sleep_hours_start or hour < self.config.sleep_hours_end
        else:
            # Same day (e.g., 1-5)
            return self.config.sleep_hours_start <= hour < self.config.sleep_hours_end
    
    def _skip_sleep_hours(self, dt: datetime) -> datetime:
        """Adjust time to skip sleep hours"""
        while self._is_sleep_hour(dt):
            dt += timedelta(hours=1)
        
        return dt


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_warmup_engine() -> WarmupPolicyEngine:
    """Helper para crear engine con config por defecto"""
    return WarmupPolicyEngine()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "WarmupPolicyConfig",
    "WarmupActionSchedule",
    "WARMUP_SCHEDULES",
    "WarmupPolicyEngine",
    "create_warmup_engine",
]
