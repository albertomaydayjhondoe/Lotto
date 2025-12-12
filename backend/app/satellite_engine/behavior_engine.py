"""
Satellite Behavior Engine - Sprint 8
Comportamiento humano simulado con anti-detección total.

Features:
- Horarios aleatorios y NO deterministas
- Jitter 20-60 min por post
- Días con variación (más/menos/sin actividad)
- Micro-pauses 18-90s entre acciones
- Bloques nocturnos personalizados
- Zero correlación entre cuentas
"""
import random
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class ActivityLevel(Enum):
    """Nivel de actividad diaria."""
    NONE = "none"          # Día de descanso
    LOW = "low"            # 1-2 posts
    MEDIUM = "medium"      # 3-5 posts
    HIGH = "high"          # 6-8 posts
    PEAK = "peak"          # 9-12 posts


@dataclass
class TimeSlot:
    """Slot de tiempo para publicación."""
    hour: int              # 0-23
    minute: int            # 0-59
    jitter_min: int        # Jitter mínimo (minutos)
    jitter_max: int        # Jitter máximo (minutos)
    
    def get_actual_time(self) -> time:
        """Obtiene hora real con jitter aplicado."""
        jitter = random.randint(self.jitter_min, self.jitter_max)
        total_minutes = self.hour * 60 + self.minute + jitter
        
        # Wrap around si excede 24h
        total_minutes = total_minutes % (24 * 60)
        
        final_hour = total_minutes // 60
        final_minute = total_minutes % 60
        
        return time(hour=final_hour, minute=final_minute)


@dataclass
class AccountSchedule:
    """Schedule personalizado de una cuenta satélite."""
    account_id: str
    platform: str          # "tiktok" | "instagram" | "youtube"
    daily_posts_target: int
    activity_pattern: List[ActivityLevel]  # Patrón semanal
    time_slots: List[TimeSlot]
    night_block_start: time  # Inicio bloque nocturno
    night_block_end: time    # Fin bloque nocturno
    timezone_offset: int     # UTC offset
    last_post_at: Optional[datetime] = None
    
    def is_night_time(self, dt: datetime) -> bool:
        """Verifica si está en bloque nocturno."""
        current_time = dt.time()
        
        if self.night_block_start < self.night_block_end:
            # Bloque normal (ej: 23:00-07:00)
            return self.night_block_start <= current_time <= self.night_block_end
        else:
            # Bloque atraviesa medianoche
            return current_time >= self.night_block_start or current_time <= self.night_block_end


@dataclass
class BehaviorPattern:
    """Patrón de comportamiento de cuenta."""
    micro_pause_min: int = 18   # Segundos
    micro_pause_max: int = 90   # Segundos
    daily_variance: float = 0.3  # 30% variación diaria
    weekly_rest_days: int = 1    # Días de descanso por semana
    consistency_score: float = 0.85  # 85% consistencia (NO perfecto)


class AntiCorrelationValidator:
    """
    Valida que NO exista correlación entre cuentas.
    
    Features:
    - Detecta publicaciones simultáneas
    - Detecta patrones repetitivos
    - Detecta sincronización sospechosa
    """
    
    def __init__(self, correlation_threshold_minutes: int = 5):
        self.correlation_threshold = correlation_threshold_minutes
        self.recent_posts: Dict[str, List[datetime]] = {}
    
    def record_post(self, account_id: str, timestamp: datetime):
        """Registra publicación de una cuenta."""
        if account_id not in self.recent_posts:
            self.recent_posts[account_id] = []
        
        self.recent_posts[account_id].append(timestamp)
        
        # Mantener solo últimas 100 publicaciones
        self.recent_posts[account_id] = self.recent_posts[account_id][-100:]
    
    def check_correlation(
        self,
        account_id: str,
        proposed_time: datetime
    ) -> Tuple[bool, List[str]]:
        """
        Verifica si el tiempo propuesto crea correlación con otras cuentas.
        
        Returns:
            (is_safe, conflicting_accounts)
        """
        conflicting = []
        
        for other_account, timestamps in self.recent_posts.items():
            if other_account == account_id:
                continue
            
            # Revisar últimas 10 publicaciones de cada cuenta
            for ts in timestamps[-10:]:
                diff_minutes = abs((proposed_time - ts).total_seconds() / 60)
                
                if diff_minutes <= self.correlation_threshold:
                    conflicting.append(other_account)
                    break
        
        is_safe = len(conflicting) == 0
        
        if not is_safe:
            logger.warning(
                f"Correlation detected: {account_id} conflicts with {conflicting} "
                f"at {proposed_time.isoformat()}"
            )
        
        return is_safe, conflicting
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas de correlación."""
        return {
            "total_accounts": len(self.recent_posts),
            "total_posts_tracked": sum(len(posts) for posts in self.recent_posts.values()),
            "correlation_threshold_minutes": self.correlation_threshold
        }


class SatelliteBehaviorEngine:
    """
    Motor de comportamiento humano para cuentas satélite.
    
    Features:
    - Genera horarios aleatorios optimizados
    - Evita patrones repetitivos
    - Asegura independencia entre cuentas
    - Simula comportamiento humano real
    """
    
    # Ritmo ideal por plataforma (posts/día)
    PLATFORM_DAILY_TARGETS = {
        "tiktok": 7,
        "instagram": 4,
        "youtube": 3
    }
    
    def __init__(self):
        self.schedules: Dict[str, AccountSchedule] = {}
        self.anti_correlation = AntiCorrelationValidator(correlation_threshold_minutes=5)
        
        logger.info("SatelliteBehaviorEngine initialized")
    
    def create_schedule(
        self,
        account_id: str,
        platform: str,
        timezone_offset: int = 0,
        custom_target: Optional[int] = None
    ) -> AccountSchedule:
        """
        Crea schedule personalizado para cuenta.
        
        Args:
            account_id: ID de cuenta satélite
            platform: tiktok/instagram/youtube
            timezone_offset: UTC offset
            custom_target: Override de posts/día (opcional)
            
        Returns:
            AccountSchedule personalizado
        """
        # Target de posts diarios
        daily_target = custom_target or self.PLATFORM_DAILY_TARGETS.get(platform, 5)
        
        # Generar patrón semanal aleatorio
        activity_pattern = self._generate_weekly_pattern()
        
        # Generar time slots con jitter
        time_slots = self._generate_time_slots(
            daily_target=daily_target,
            platform=platform
        )
        
        # Bloque nocturno aleatorio
        night_start_hour = random.randint(22, 23)
        night_end_hour = random.randint(6, 8)
        
        schedule = AccountSchedule(
            account_id=account_id,
            platform=platform,
            daily_posts_target=daily_target,
            activity_pattern=activity_pattern,
            time_slots=time_slots,
            night_block_start=time(hour=night_start_hour, minute=random.randint(0, 59)),
            night_block_end=time(hour=night_end_hour, minute=random.randint(0, 59)),
            timezone_offset=timezone_offset
        )
        
        self.schedules[account_id] = schedule
        
        logger.info(
            f"Schedule created for {account_id}: "
            f"platform={platform}, target={daily_target}/day, "
            f"night={night_start_hour}:00-{night_end_hour}:00"
        )
        
        return schedule
    
    def _generate_weekly_pattern(self) -> List[ActivityLevel]:
        """
        Genera patrón semanal aleatorio (7 días).
        
        Returns:
            Lista de 7 ActivityLevel (uno por día)
        """
        pattern = []
        
        # Asegurar al menos 1 día de descanso
        rest_day = random.randint(0, 6)
        
        for day in range(7):
            if day == rest_day:
                pattern.append(ActivityLevel.NONE)
            else:
                # Distribución realista
                roll = random.random()
                if roll < 0.15:
                    pattern.append(ActivityLevel.LOW)
                elif roll < 0.50:
                    pattern.append(ActivityLevel.MEDIUM)
                elif roll < 0.85:
                    pattern.append(ActivityLevel.HIGH)
                else:
                    pattern.append(ActivityLevel.PEAK)
        
        return pattern
    
    def _generate_time_slots(
        self,
        daily_target: int,
        platform: str
    ) -> List[TimeSlot]:
        """
        Genera time slots aleatorios para el día.
        
        Args:
            daily_target: Número de posts objetivo
            platform: Plataforma
            
        Returns:
            Lista de TimeSlot con jitter
        """
        slots = []
        
        # Dividir el día en ventanas (~16h activas, 8h noche)
        # Ventanas de publicación: 7am-11pm (16 horas)
        active_hours = list(range(7, 23))
        
        # Seleccionar horas aleatorias
        selected_hours = random.sample(active_hours, min(daily_target, len(active_hours)))
        selected_hours.sort()
        
        for hour in selected_hours:
            # Minuto aleatorio
            minute = random.randint(0, 59)
            
            # Jitter 20-60 min
            jitter_min = random.randint(20, 40)
            jitter_max = random.randint(40, 60)
            
            slot = TimeSlot(
                hour=hour,
                minute=minute,
                jitter_min=jitter_min,
                jitter_max=jitter_max
            )
            
            slots.append(slot)
        
        return slots
    
    def get_next_post_time(
        self,
        account_id: str,
        current_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Obtiene próxima hora de publicación para cuenta.
        
        Args:
            account_id: ID de cuenta
            current_time: Tiempo actual (default: now)
            
        Returns:
            Datetime de próxima publicación o None si no disponible
        """
        if account_id not in self.schedules:
            logger.warning(f"No schedule found for {account_id}")
            return None
        
        schedule = self.schedules[account_id]
        now = current_time or datetime.utcnow()
        
        # Verificar actividad del día actual
        day_of_week = now.weekday()
        activity = schedule.activity_pattern[day_of_week]
        
        if activity == ActivityLevel.NONE:
            logger.debug(f"{account_id} is on rest day ({day_of_week})")
            return None
        
        # Buscar próximo slot disponible
        for slot in schedule.time_slots:
            slot_time = slot.get_actual_time()
            
            # Combinar fecha + hora
            proposed_dt = datetime.combine(now.date(), slot_time)
            
            # Si ya pasó hoy, mover a mañana
            if proposed_dt <= now:
                proposed_dt += timedelta(days=1)
            
            # Verificar que no esté en bloque nocturno
            if schedule.is_night_time(proposed_dt):
                continue
            
            # Verificar anti-correlación
            is_safe, conflicts = self.anti_correlation.check_correlation(
                account_id=account_id,
                proposed_time=proposed_dt
            )
            
            if is_safe:
                return proposed_dt
            else:
                # Agregar jitter adicional para evitar conflicto
                proposed_dt += timedelta(minutes=random.randint(10, 30))
        
        # Si no hay slots disponibles hoy, intentar mañana
        tomorrow = now + timedelta(days=1)
        return self.get_next_post_time(account_id, tomorrow)
    
    def register_post(
        self,
        account_id: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Registra publicación realizada.
        
        Args:
            account_id: ID de cuenta
            timestamp: Timestamp de publicación
        """
        ts = timestamp or datetime.utcnow()
        
        # Actualizar schedule
        if account_id in self.schedules:
            self.schedules[account_id].last_post_at = ts
        
        # Registrar en anti-correlación
        self.anti_correlation.record_post(account_id, ts)
        
        logger.info(f"Post registered: {account_id} at {ts.isoformat()}")
    
    def get_micro_pause(self) -> int:
        """
        Obtiene pausa micro-aleatoria entre acciones.
        
        Returns:
            Segundos de pausa (18-90s)
        """
        return random.randint(18, 90)
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del behavior engine."""
        return {
            "total_schedules": len(self.schedules),
            "platforms": {
                platform: len([s for s in self.schedules.values() if s.platform == platform])
                for platform in ["tiktok", "instagram", "youtube"]
            },
            "anti_correlation": self.anti_correlation.get_stats()
        }
