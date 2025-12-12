"""
SPRINT 12.1 - Human-Assisted Warm-Up Scheduler
Module: Human Warmup Scheduler

Generación diaria de tareas humanas obligatorias durante warmup.
NO automatiza acciones - solo genera el plan que un humano debe ejecutar.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .account_models import AccountState, ActionType

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class HumanWarmupSchedulerConfig:
    """Configuración del scheduler de warmup humano"""
    
    # Scroll durations (seconds) - min, max
    scroll_duration_w1_3: tuple[int, int] = (180, 360)  # 3-6 min
    scroll_duration_w4_7: tuple[int, int] = (240, 480)  # 4-8 min
    scroll_duration_w8_14: tuple[int, int] = (300, 600)  # 5-10 min
    
    # Action counts by phase
    likes_w1_3: tuple[int, int] = (2, 4)
    likes_w4_7: tuple[int, int] = (3, 6)
    likes_w8_14: tuple[int, int] = (4, 8)
    
    comments_w1_3: tuple[int, int] = (0, 1)  # Occasional
    comments_w4_7: tuple[int, int] = (1, 2)
    comments_w8_14: tuple[int, int] = (1, 3)
    
    follows_w4_7: tuple[int, int] = (0, 1)
    follows_w8_14: tuple[int, int] = (1, 2)
    
    posts_w8_14: tuple[int, int] = (0, 1)  # First post in W8-14
    
    # Intervals (seconds) - min, max
    like_interval: tuple[int, int] = (20, 90)  # 20-90s between likes
    comment_interval: tuple[int, int] = (60, 180)  # 1-3min
    
    # Session timing
    min_session_duration: int = 180  # 3 min minimum
    max_session_duration: int = 1200  # 20 min maximum
    
    # Verification
    verification_deadline_hours: int = 24  # Complete within 24h
    
    # Risk checks
    risk_check_enabled: bool = True


# ============================================================================
# HUMAN WARMUP TASK
# ============================================================================

@dataclass
class HumanWarmupAction:
    """Acción humana individual"""
    
    action_type: str  # scroll, like, comment, follow, post
    quantity: Optional[int] = None
    duration_seconds: Optional[int] = None
    interval_seconds: Optional[tuple[int, int]] = None
    style: str = "natural"  # natural, casual, deliberate
    instructions: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "type": self.action_type,
            "quantity": self.quantity,
            "duration": f"{self.duration_seconds}s" if self.duration_seconds else None,
            "interval": f"{self.interval_seconds[0]}-{self.interval_seconds[1]}s" if self.interval_seconds else None,
            "style": self.style,
            "instructions": self.instructions
        }


@dataclass
class HumanWarmupTask:
    """Tarea completa de warmup humano para un día"""
    
    task_id: str
    account_id: str
    warmup_day: int
    warmup_phase: AccountState
    created_at: datetime = field(default_factory=datetime.now)
    
    # Required actions
    required_actions: List[HumanWarmupAction] = field(default_factory=list)
    
    # Timing
    suggested_start_time: Optional[datetime] = None
    verification_deadline: Optional[datetime] = None
    
    # Checks
    risk_checks_required: bool = True
    fingerprint_stability_check: bool = True
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, failed, expired
    completed_at: Optional[datetime] = None
    verification_result: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "account_id": self.account_id,
            "day": self.warmup_day,
            "phase": self.warmup_phase.value,
            "required_actions": [action.to_dict() for action in self.required_actions],
            "suggested_start_time": self.suggested_start_time.isoformat() if self.suggested_start_time else None,
            "verification_deadline": self.verification_deadline.isoformat() if self.verification_deadline else None,
            "risk_checks_required": self.risk_checks_required,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# ============================================================================
# HUMAN WARMUP SCHEDULER
# ============================================================================

class HumanWarmupScheduler:
    """
    Scheduler de tareas humanas para warmup.
    
    Responsabilidades:
    - Generar tareas diarias basadas en estado
    - Sugerir timing óptimo
    - Trackear completación
    - Verificar deadlines
    
    NO automatiza - solo planifica.
    """
    
    def __init__(self, config: Optional[HumanWarmupSchedulerConfig] = None):
        self.config = config or HumanWarmupSchedulerConfig()
        
        # Task storage
        self._tasks: Dict[str, List[HumanWarmupTask]] = {}  # account_id -> [tasks]
        
        logger.info("HumanWarmupScheduler initialized")
    
    # ========================================================================
    # PUBLIC API - TASK GENERATION
    # ========================================================================
    
    def generate_daily_task(
        self,
        account_id: str,
        warmup_day: int,
        warmup_phase: AccountState,
        preferred_hours: Optional[List[int]] = None
    ) -> HumanWarmupTask:
        """
        Genera tarea diaria de warmup humano.
        
        Args:
            account_id: ID de la cuenta
            warmup_day: Día de warmup (1-14)
            warmup_phase: Estado actual (W1_3, W4_7, W8_14)
            preferred_hours: Horas preferidas (default: 9-21)
        
        Returns:
            HumanWarmupTask con acciones requeridas
        """
        import uuid
        
        task_id = f"hwt_{uuid.uuid4().hex[:12]}"
        
        # Generate actions based on phase
        actions = self._generate_actions_for_phase(warmup_phase)
        
        # Calculate suggested timing
        if preferred_hours is None:
            preferred_hours = list(range(9, 22))  # 9 AM - 9 PM
        
        suggested_hour = random.choice(preferred_hours)
        suggested_start = datetime.now().replace(
            hour=suggested_hour,
            minute=random.randint(0, 59),
            second=0,
            microsecond=0
        )
        
        # If time already passed, schedule for tomorrow
        if suggested_start < datetime.now():
            suggested_start += timedelta(days=1)
        
        # Verification deadline
        deadline = suggested_start + timedelta(hours=self.config.verification_deadline_hours)
        
        task = HumanWarmupTask(
            task_id=task_id,
            account_id=account_id,
            warmup_day=warmup_day,
            warmup_phase=warmup_phase,
            required_actions=actions,
            suggested_start_time=suggested_start,
            verification_deadline=deadline,
            risk_checks_required=self.config.risk_check_enabled,
            fingerprint_stability_check=True
        )
        
        # Store task
        if account_id not in self._tasks:
            self._tasks[account_id] = []
        self._tasks[account_id].append(task)
        
        logger.info(f"Generated warmup task for {account_id} (day {warmup_day}): {len(actions)} actions")
        
        return task
    
    def get_pending_tasks(self, account_id: str) -> List[HumanWarmupTask]:
        """Obtiene tareas pendientes para una cuenta"""
        tasks = self._tasks.get(account_id, [])
        return [t for t in tasks if t.status == "pending"]
    
    def get_task(self, task_id: str) -> Optional[HumanWarmupTask]:
        """Obtiene una tarea por ID"""
        for tasks in self._tasks.values():
            for task in tasks:
                if task.task_id == task_id:
                    return task
        return None
    
    def mark_task_started(self, task_id: str):
        """Marca tarea como iniciada"""
        task = self.get_task(task_id)
        if task:
            task.status = "in_progress"
            logger.info(f"Task {task_id} started")
    
    def mark_task_completed(
        self,
        task_id: str,
        verification_result: Dict
    ):
        """Marca tarea como completada con resultado de verificación"""
        task = self.get_task(task_id)
        if task:
            task.status = "completed"
            task.completed_at = datetime.now()
            task.verification_result = verification_result
            logger.info(f"Task {task_id} completed")
    
    def mark_task_failed(self, task_id: str, reason: str = ""):
        """Marca tarea como fallida"""
        task = self.get_task(task_id)
        if task:
            task.status = "failed"
            task.verification_result = {"failed": True, "reason": reason}
            logger.warning(f"Task {task_id} failed: {reason}")
    
    def check_expired_tasks(self) -> List[str]:
        """Verifica y marca tareas expiradas"""
        now = datetime.now()
        expired = []
        
        for tasks in self._tasks.values():
            for task in tasks:
                if task.status == "pending" and task.verification_deadline:
                    if now > task.verification_deadline:
                        task.status = "expired"
                        expired.append(task.task_id)
                        logger.warning(f"Task {task.task_id} expired")
        
        return expired
    
    # ========================================================================
    # PUBLIC API - STATISTICS
    # ========================================================================
    
    def get_completion_rate(self, account_id: str) -> float:
        """
        Calcula tasa de completación de tareas.
        
        Returns:
            Porcentaje 0.0-1.0
        """
        tasks = self._tasks.get(account_id, [])
        if not tasks:
            return 0.0
        
        completed = len([t for t in tasks if t.status == "completed"])
        return completed / len(tasks)
    
    def get_task_history(self, account_id: str) -> List[HumanWarmupTask]:
        """Obtiene historial completo de tareas"""
        return self._tasks.get(account_id, [])
    
    def get_summary(self, account_id: str) -> Dict:
        """Obtiene resumen de warmup"""
        tasks = self._tasks.get(account_id, [])
        
        return {
            "total_tasks": len(tasks),
            "completed": len([t for t in tasks if t.status == "completed"]),
            "pending": len([t for t in tasks if t.status == "pending"]),
            "failed": len([t for t in tasks if t.status == "failed"]),
            "expired": len([t for t in tasks if t.status == "expired"]),
            "completion_rate": self.get_completion_rate(account_id)
        }
    
    # ========================================================================
    # INTERNAL - ACTION GENERATION
    # ========================================================================
    
    def _generate_actions_for_phase(
        self,
        phase: AccountState
    ) -> List[HumanWarmupAction]:
        """Genera acciones según la fase de warmup"""
        
        actions = []
        
        if phase == AccountState.W1_3:
            # Scroll
            duration = random.randint(*self.config.scroll_duration_w1_3)
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=duration,
                style="casual",
                instructions="Scroll naturally through feed, pause on interesting content"
            ))
            
            # Likes
            likes_count = random.randint(*self.config.likes_w1_3)
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=likes_count,
                interval_seconds=self.config.like_interval,
                style="natural",
                instructions=f"Like {likes_count} posts with natural intervals (20-90s)"
            ))
            
            # Comments (occasional)
            if random.random() < 0.3:  # 30% chance
                actions.append(HumanWarmupAction(
                    action_type="comment",
                    quantity=1,
                    style="natural",
                    instructions="Leave 1 natural, short comment (emoji or 2-3 words)"
                ))
        
        elif phase == AccountState.W4_7:
            # Scroll
            duration = random.randint(*self.config.scroll_duration_w4_7)
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=duration,
                style="deliberate",
                instructions="Browse feed with more engagement, spend time on videos"
            ))
            
            # Likes
            likes_count = random.randint(*self.config.likes_w4_7)
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=likes_count,
                interval_seconds=self.config.like_interval,
                style="natural",
                instructions=f"Like {likes_count} posts naturally"
            ))
            
            # Comments
            comments_count = random.randint(*self.config.comments_w4_7)
            if comments_count > 0:
                actions.append(HumanWarmupAction(
                    action_type="comment",
                    quantity=comments_count,
                    style="natural",
                    instructions=f"Leave {comments_count} genuine comment(s) on relevant content"
                ))
            
            # Follows (occasional)
            if random.random() < 0.4:  # 40% chance
                follows_count = random.randint(*self.config.follows_w4_7)
                if follows_count > 0:
                    actions.append(HumanWarmupAction(
                        action_type="follow",
                        quantity=follows_count,
                        style="natural",
                        instructions=f"Follow {follows_count} account(s) relevant to your niche"
                    ))
        
        elif phase == AccountState.W8_14:
            # Scroll
            duration = random.randint(*self.config.scroll_duration_w8_14)
            actions.append(HumanWarmupAction(
                action_type="scroll",
                duration_seconds=duration,
                style="engaged",
                instructions="Active browsing with diverse interactions"
            ))
            
            # Likes
            likes_count = random.randint(*self.config.likes_w8_14)
            actions.append(HumanWarmupAction(
                action_type="like",
                quantity=likes_count,
                interval_seconds=self.config.like_interval,
                style="natural",
                instructions=f"Like {likes_count} posts with variety"
            ))
            
            # Comments
            comments_count = random.randint(*self.config.comments_w8_14)
            if comments_count > 0:
                actions.append(HumanWarmupAction(
                    action_type="comment",
                    quantity=comments_count,
                    style="natural",
                    instructions=f"Leave {comments_count} thoughtful comment(s)"
                ))
            
            # Follows
            follows_count = random.randint(*self.config.follows_w8_14)
            if follows_count > 0:
                actions.append(HumanWarmupAction(
                    action_type="follow",
                    quantity=follows_count,
                    style="natural",
                    instructions=f"Follow {follows_count} account(s)"
                ))
            
            # First post (occasional)
            if random.random() < 0.3:  # 30% chance
                actions.append(HumanWarmupAction(
                    action_type="post",
                    quantity=1,
                    style="natural",
                    instructions="Create and post your first piece of content (keep it simple and on-niche)"
                ))
        
        return actions


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "HumanWarmupSchedulerConfig",
    "HumanWarmupAction",
    "HumanWarmupTask",
    "HumanWarmupScheduler",
]
