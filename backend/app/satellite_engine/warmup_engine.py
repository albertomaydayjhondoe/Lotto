"""
Satellite Warmup Engine - Sprint 8
Warm-up dinámico con jitter aleatorio para nuevas cuentas.

NO calendarios fijos. Cada cuenta tiene su propio ritmo progresivo.
Días 1-5 con incremento gradual + jitter para anti-detección.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class WarmupPhase(Enum):
    """Fases del warm-up."""
    DAY_1 = "day_1"      # 1 post
    DAY_2 = "day_2"      # 1-2 posts
    DAY_3 = "day_3"      # 2-3 posts
    DAY_4 = "day_4"      # 3-4 posts
    DAY_5 = "day_5"      # 4-5 posts
    FULL_SPEED = "full_speed"  # Máximo (7/4/3 según plataforma)
    COMPLETED = "completed"


@dataclass
class WarmupSchedule:
    """Schedule diario para warm-up."""
    day: int
    phase: WarmupPhase
    target_posts: int
    actual_posts: int = 0
    post_times: List[datetime] = field(default_factory=list)
    jitter_applied: bool = True
    
    def is_complete(self) -> bool:
        """Verifica si el día está completo."""
        return self.actual_posts >= self.target_posts
    
    def remaining_posts(self) -> int:
        """Posts restantes del día."""
        return max(0, self.target_posts - self.actual_posts)


@dataclass
class WarmupPlan:
    """Plan completo de warm-up para una cuenta."""
    account_id: str
    platform: str
    start_date: datetime
    current_day: int = 1
    current_phase: WarmupPhase = WarmupPhase.DAY_1
    
    daily_schedules: List[WarmupSchedule] = field(default_factory=list)
    completed_days: List[int] = field(default_factory=list)
    
    total_posts_published: int = 0
    warmup_completed: bool = False
    completed_at: Optional[datetime] = None
    
    def get_current_schedule(self) -> Optional[WarmupSchedule]:
        """Obtiene schedule del día actual."""
        for schedule in self.daily_schedules:
            if schedule.day == self.current_day:
                return schedule
        return None
    
    def advance_day(self):
        """Avanza al siguiente día."""
        self.completed_days.append(self.current_day)
        self.current_day += 1
        
        # Update phase
        if self.current_day == 2:
            self.current_phase = WarmupPhase.DAY_2
        elif self.current_day == 3:
            self.current_phase = WarmupPhase.DAY_3
        elif self.current_day == 4:
            self.current_phase = WarmupPhase.DAY_4
        elif self.current_day == 5:
            self.current_phase = WarmupPhase.DAY_5
        elif self.current_day >= 6:
            self.current_phase = WarmupPhase.FULL_SPEED
            self.warmup_completed = True
            self.completed_at = datetime.now()
            
        logger.info(f"Account {self.account_id} advanced to day {self.current_day} ({self.current_phase.value})")


class SatelliteWarmupEngine:
    """
    Motor de warm-up dinámico para cuentas satélite.
    
    Features:
    - Warm-up progresivo días 1-5
    - Jitter aleatorio en horarios
    - NO calendarios fijos
    - Personalizado por cuenta
    - Anti-detección integrado
    """
    
    # Rangos de posts por día (min, max)
    WARMUP_RANGES = {
        WarmupPhase.DAY_1: (1, 1),
        WarmupPhase.DAY_2: (1, 2),
        WarmupPhase.DAY_3: (2, 3),
        WarmupPhase.DAY_4: (3, 4),
        WarmupPhase.DAY_5: (4, 5),
    }
    
    # Full speed targets por plataforma
    FULL_SPEED_TARGETS = {
        "tiktok": 7,
        "instagram": 4,
        "youtube": 3
    }
    
    def __init__(self):
        self.active_plans: Dict[str, WarmupPlan] = {}
        
        logger.info("SatelliteWarmupEngine initialized")
    
    def create_warmup_plan(
        self,
        account_id: str,
        platform: str,
        start_date: Optional[datetime] = None
    ) -> WarmupPlan:
        """
        Crea plan de warm-up para cuenta nueva.
        
        Args:
            account_id: ID de cuenta
            platform: Plataforma (tiktok/instagram/youtube)
            start_date: Fecha de inicio (default: now)
            
        Returns:
            WarmupPlan personalizado
        """
        if platform not in self.FULL_SPEED_TARGETS:
            raise ValueError(f"Platform {platform} not supported")
        
        start_date = start_date or datetime.now()
        
        plan = WarmupPlan(
            account_id=account_id,
            platform=platform,
            start_date=start_date
        )
        
        # Generate schedules for days 1-5
        for day in range(1, 6):
            phase = self._get_phase_for_day(day)
            target = self._calculate_daily_target(phase)
            
            schedule = WarmupSchedule(
                day=day,
                phase=phase,
                target_posts=target
            )
            
            # Generate post times with jitter
            post_times = self._generate_post_times(
                start_date + timedelta(days=day - 1),
                target
            )
            schedule.post_times = post_times
            
            plan.daily_schedules.append(schedule)
        
        # Store plan
        self.active_plans[account_id] = plan
        
        logger.info(f"Created warmup plan for {account_id} on {platform} (5 days)")
        return plan
    
    def _get_phase_for_day(self, day: int) -> WarmupPhase:
        """Obtiene fase para día específico."""
        if day == 1:
            return WarmupPhase.DAY_1
        elif day == 2:
            return WarmupPhase.DAY_2
        elif day == 3:
            return WarmupPhase.DAY_3
        elif day == 4:
            return WarmupPhase.DAY_4
        elif day == 5:
            return WarmupPhase.DAY_5
        else:
            return WarmupPhase.FULL_SPEED
    
    def _calculate_daily_target(self, phase: WarmupPhase) -> int:
        """
        Calcula target diario con variación aleatoria.
        
        NO targets fijos - cada día puede variar dentro del rango.
        """
        if phase not in self.WARMUP_RANGES:
            return 1
        
        min_posts, max_posts = self.WARMUP_RANGES[phase]
        return random.randint(min_posts, max_posts)
    
    def _generate_post_times(
        self,
        base_date: datetime,
        num_posts: int
    ) -> List[datetime]:
        """
        Genera horarios de posts con jitter aleatorio.
        
        Args:
            base_date: Fecha base
            num_posts: Número de posts
            
        Returns:
            Lista de datetimes con jitter aplicado
        """
        # Prime hours: 9-22
        available_hours = list(range(9, 23))
        
        # Shuffle for randomness
        random.shuffle(available_hours)
        
        # Select hours
        selected_hours = available_hours[:num_posts]
        selected_hours.sort()
        
        post_times = []
        for hour in selected_hours:
            # Add jitter: ±30 minutes
            jitter_minutes = random.randint(-30, 30)
            
            post_time = base_date.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            ) + timedelta(minutes=jitter_minutes)
            
            post_times.append(post_time)
        
        return post_times
    
    def get_next_post_time(self, account_id: str) -> Optional[datetime]:
        """
        Obtiene próximo horario de post para cuenta en warm-up.
        
        Args:
            account_id: ID de cuenta
            
        Returns:
            Datetime del próximo post o None si plan completo
        """
        plan = self.active_plans.get(account_id)
        if not plan:
            logger.warning(f"No warmup plan for {account_id}")
            return None
        
        if plan.warmup_completed:
            logger.info(f"Warmup completed for {account_id}")
            return None
        
        # Get current schedule
        schedule = plan.get_current_schedule()
        if not schedule:
            logger.error(f"No schedule for day {plan.current_day}")
            return None
        
        # Check if day complete
        if schedule.is_complete():
            # Advance to next day
            plan.advance_day()
            return self.get_next_post_time(account_id)
        
        # Next post time from schedule
        next_index = schedule.actual_posts
        if next_index < len(schedule.post_times):
            return schedule.post_times[next_index]
        
        return None
    
    def register_post(self, account_id: str, post_time: datetime):
        """
        Registra post publicado durante warm-up.
        
        Args:
            account_id: ID de cuenta
            post_time: Timestamp del post
        """
        plan = self.active_plans.get(account_id)
        if not plan:
            logger.warning(f"No warmup plan for {account_id}")
            return
        
        schedule = plan.get_current_schedule()
        if not schedule:
            return
        
        schedule.actual_posts += 1
        plan.total_posts_published += 1
        
        logger.info(f"Registered post for {account_id}: day {plan.current_day}, {schedule.actual_posts}/{schedule.target_posts}")
        
        # Check if day complete
        if schedule.is_complete():
            logger.info(f"Day {plan.current_day} complete for {account_id}")
    
    def get_plan(self, account_id: str) -> Optional[WarmupPlan]:
        """Obtiene plan de warm-up de cuenta."""
        return self.active_plans.get(account_id)
    
    def is_in_warmup(self, account_id: str) -> bool:
        """Verifica si cuenta está en warm-up."""
        plan = self.active_plans.get(account_id)
        if not plan:
            return False
        return not plan.warmup_completed
    
    def get_warmup_progress(self, account_id: str) -> Dict[str, any]:
        """
        Obtiene progreso de warm-up.
        
        Returns:
            Dict con current_day, phase, posts_today, total_posts, completed
        """
        plan = self.active_plans.get(account_id)
        if not plan:
            return {"error": "No warmup plan"}
        
        schedule = plan.get_current_schedule()
        
        return {
            "account_id": account_id,
            "platform": plan.platform,
            "current_day": plan.current_day,
            "current_phase": plan.current_phase.value,
            "posts_today": schedule.actual_posts if schedule else 0,
            "target_today": schedule.target_posts if schedule else 0,
            "total_posts": plan.total_posts_published,
            "completed_days": plan.completed_days,
            "warmup_completed": plan.warmup_completed,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
        }
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del warmup engine."""
        total_plans = len(self.active_plans)
        completed = sum(1 for p in self.active_plans.values() if p.warmup_completed)
        in_progress = total_plans - completed
        
        return {
            "total_plans": total_plans,
            "in_progress": in_progress,
            "completed": completed,
            "accounts_by_phase": {
                phase.value: sum(
                    1 for p in self.active_plans.values()
                    if p.current_phase == phase
                )
                for phase in WarmupPhase
            }
        }
