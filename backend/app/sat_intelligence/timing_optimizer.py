"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Timing Optimizer

Optimizador de timing que:
- Encuentra ventanas óptimas basadas en ML learnings
- Aplica gaussian jitter para evitar patrones detectables
- Reduce pattern similarity estadísticamente
- Respeta warmup phases y rate limits
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from .sat_intel_contracts import (
    TimingWindow,
    AccountProfile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class TimingConfig:
    """Configuración del timing optimizer"""
    
    # Gaussian jitter parameters
    jitter_mean_minutes: float = 0.0
    jitter_std_minutes: float = 15.0  # ±15 min std deviation
    jitter_max_minutes: float = 45.0  # Cap at ±45 min
    
    # Pattern similarity threshold
    max_pattern_similarity: float = 0.7
    min_time_gap_hours: float = 2.0
    
    # Optimal window scoring
    audience_peak_weight: float = 0.4
    competition_weight: float = 0.3
    consistency_weight: float = 0.3
    
    # Warmup constraints
    warmup_max_posts_per_day: int = 2
    warmup_min_gap_hours: int = 6


# ============================================================================
# TIMING OPTIMIZER
# ============================================================================

class TimingOptimizer:
    """
    Optimizador de timing con gaussian jitter y pattern reduction.
    
    Flujo:
    1. Identifica ventanas óptimas basadas en account profile
    2. Aplica gaussian jitter a cada ventana
    3. Verifica que no haya pattern similarity con posts recientes
    4. Respeta warmup constraints si aplica
    5. Retorna TimingWindow con scores y reasoning
    """
    
    def __init__(self, config: Optional[TimingConfig] = None):
        self.config = config or TimingConfig()
        self._rng = random.Random()
        logger.info(f"TimingOptimizer initialized with jitter std={self.config.jitter_std_minutes}min")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def find_optimal_window(
        self,
        account: AccountProfile,
        target_time: datetime,
        duration_hours: int = 24
    ) -> TimingWindow:
        """
        Encuentra la ventana óptima para publicar en las próximas N horas.
        
        Args:
            account: Perfil de la cuenta
            target_time: Tiempo desde el cual buscar
            duration_hours: Duración de la ventana de búsqueda
        
        Returns:
            TimingWindow con timing óptimo y jitter aplicado
        """
        logger.debug(f"Finding optimal window for account {account.account_id} "
                    f"starting at {target_time}, duration={duration_hours}h")
        
        # 1. Generar candidatos de ventanas óptimas
        candidates = self._generate_candidate_windows(account, target_time, duration_hours)
        
        # 2. Score cada candidato
        scored_candidates = [
            (window, self._score_window(window, account, target_time))
            for window in candidates
        ]
        
        # 3. Seleccionar mejor candidato
        if not scored_candidates:
            # Fallback: target_time + jitter
            return self._create_fallback_window(target_time, account)
        
        best_window, best_score = max(scored_candidates, key=lambda x: x[1])
        
        # 4. Aplicar gaussian jitter
        jittered_window = self._apply_jitter(best_window, account)
        
        # 5. Verificar pattern similarity
        if self._check_pattern_similarity(jittered_window, account):
            logger.warning(f"Pattern similarity detected for {account.account_id}, applying extra jitter")
            jittered_window = self._apply_extra_jitter(jittered_window, account)
        
        logger.debug(f"Selected window: {jittered_window.start_time}, score={jittered_window.optimal_score:.2f}")
        return jittered_window
    
    def batch_find_windows(
        self,
        accounts: List[AccountProfile],
        target_time: datetime,
        duration_hours: int = 24,
        ensure_diversity: bool = True
    ) -> Dict[str, TimingWindow]:
        """
        Encuentra ventanas óptimas para múltiples cuentas.
        
        Si ensure_diversity=True, garantiza que las ventanas no estén
        demasiado cerca entre sí (anti-pattern).
        """
        windows = {}
        used_times = []
        
        for account in accounts:
            window = self.find_optimal_window(account, target_time, duration_hours)
            
            # Check diversity si está habilitado
            if ensure_diversity and used_times:
                while self._too_close_to_existing(window.start_time, used_times):
                    # Re-aplicar jitter
                    logger.debug(f"Window too close to existing, re-jittering for {account.account_id}")
                    window = self._apply_extra_jitter(window, account)
            
            windows[account.account_id] = window
            used_times.append(window.start_time)
        
        logger.info(f"Generated {len(windows)} timing windows with diversity={ensure_diversity}")
        return windows
    
    def calculate_pattern_similarity(
        self,
        windows: List[datetime],
        lookback_hours: int = 168  # 1 semana
    ) -> float:
        """
        Calcula pattern similarity entre ventanas de tiempo.
        
        Retorna score 0-1:
        - 0 = completamente random, no hay patrón
        - 1 = patrón perfecto, muy predecible
        
        Usa análisis estadístico de gaps entre posts.
        """
        if len(windows) < 2:
            return 0.0
        
        # Ordenar ventanas
        sorted_windows = sorted(windows)
        
        # Calcular gaps en horas
        gaps = [
            (sorted_windows[i+1] - sorted_windows[i]).total_seconds() / 3600
            for i in range(len(sorted_windows) - 1)
        ]
        
        if not gaps:
            return 0.0
        
        # Calcular estadísticas
        mean_gap = sum(gaps) / len(gaps)
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        std_dev = math.sqrt(variance)
        
        # Coefficient of variation (CV)
        # CV bajo = gaps muy consistentes = patrón alto
        # CV alto = gaps muy variados = patrón bajo
        if mean_gap == 0:
            return 1.0  # Todos al mismo tiempo = patrón perfecto
        
        cv = std_dev / mean_gap
        
        # Normalizar CV a [0, 1]
        # CV ~ 0 → similarity ~ 1
        # CV ~ 1+ → similarity ~ 0
        similarity = max(0.0, min(1.0, 1.0 - cv))
        
        logger.debug(f"Pattern similarity: {similarity:.3f} (CV={cv:.3f}, mean_gap={mean_gap:.1f}h)")
        return similarity
    
    # ========================================================================
    # WINDOW GENERATION
    # ========================================================================
    
    def _generate_candidate_windows(
        self,
        account: AccountProfile,
        start_time: datetime,
        duration_hours: int
    ) -> List[TimingWindow]:
        """Genera ventanas candidatas basadas en optimal hours"""
        candidates = []
        
        # Si no hay optimal hours, usar ventanas cada 4 horas
        if not account.optimal_hours:
            for hours_offset in range(0, duration_hours, 4):
                window_time = start_time + timedelta(hours=hours_offset)
                candidates.append(self._create_window(window_time, account))
            return candidates
        
        # Usar optimal hours del account
        current = start_time
        end_time = start_time + timedelta(hours=duration_hours)
        
        while current < end_time:
            current_hour = current.hour
            
            # Check si current_hour está en optimal_hours
            if current_hour in account.optimal_hours:
                # Check warmup constraints
                if account.warmup_day > 0 and account.warmup_day < 14:
                    if self._respects_warmup_constraints(current, account):
                        candidates.append(self._create_window(current, account))
                else:
                    candidates.append(self._create_window(current, account))
            
            current += timedelta(hours=1)
        
        return candidates
    
    def _create_window(self, start_time: datetime, account: AccountProfile) -> TimingWindow:
        """Crea TimingWindow base sin jitter"""
        end_time = start_time + timedelta(minutes=30)  # 30-min window
        
        # Score inicial (será refinado en _score_window)
        optimal_score = 0.7
        competition_score = 0.6
        audience_score = 0.8
        
        return TimingWindow(
            start_time=start_time,
            end_time=end_time,
            optimal_score=optimal_score,
            competition_score=competition_score,
            audience_score=audience_score,
            jitter_minutes=0.0,
            reasoning="Initial window"
        )
    
    def _create_fallback_window(self, target_time: datetime, account: AccountProfile) -> TimingWindow:
        """Crea ventana fallback cuando no hay candidatos"""
        logger.warning(f"No candidates found, using fallback window for {account.account_id}")
        
        window = self._create_window(target_time, account)
        window.optimal_score = 0.5
        window.reasoning = "Fallback window (no optimal hours data)"
        
        return self._apply_jitter(window, account)
    
    # ========================================================================
    # WINDOW SCORING
    # ========================================================================
    
    def _score_window(self, window: TimingWindow, account: AccountProfile, current_time: datetime) -> float:
        """Score una ventana candidata"""
        
        # 1. Audience score: qué tan cerca está de optimal hours
        hour = window.start_time.hour
        if account.optimal_hours and hour in account.optimal_hours:
            audience_score = 1.0
        else:
            # Decay basado en distancia a optimal hour más cercano
            if account.optimal_hours:
                min_distance = min(abs(hour - oh) for oh in account.optimal_hours)
                audience_score = max(0.0, 1.0 - (min_distance / 12.0))
            else:
                audience_score = 0.7
        
        # 2. Competition score: menos competencia es mejor
        # Heurística: horas tempranas (6-9am) y tarde (8-11pm) tienen menos competencia
        if 6 <= hour <= 9 or 20 <= hour <= 23:
            competition_score = 0.8
        else:
            competition_score = 0.5
        
        # 3. Consistency score: qué tan consistente con historial
        consistency_score = 0.7
        if account.last_post_at:
            hours_since_last = (window.start_time - account.last_post_at).total_seconds() / 3600
            
            # Ideal gap: 12-24 horas
            if 12 <= hours_since_last <= 24:
                consistency_score = 1.0
            elif hours_since_last < 12:
                consistency_score = max(0.3, hours_since_last / 12.0)
            else:
                consistency_score = max(0.5, 1.0 - ((hours_since_last - 24) / 48.0))
        
        # Combine con pesos
        total_score = (
            audience_score * self.config.audience_peak_weight +
            competition_score * self.config.competition_weight +
            consistency_score * self.config.consistency_weight
        )
        
        # Update window scores
        window.audience_score = audience_score
        window.competition_score = competition_score
        window.optimal_score = total_score
        
        return total_score
    
    # ========================================================================
    # JITTER APPLICATION
    # ========================================================================
    
    def _apply_jitter(self, window: TimingWindow, account: AccountProfile) -> TimingWindow:
        """Aplica gaussian jitter a una ventana"""
        
        # Generate gaussian jitter
        jitter_minutes = self._rng.gauss(
            self.config.jitter_mean_minutes,
            self.config.jitter_std_minutes
        )
        
        # Cap jitter
        jitter_minutes = max(
            -self.config.jitter_max_minutes,
            min(self.config.jitter_max_minutes, jitter_minutes)
        )
        
        # Apply jitter
        jittered_start = window.start_time + timedelta(minutes=jitter_minutes)
        jittered_end = window.end_time + timedelta(minutes=jitter_minutes)
        
        # Update window
        window.start_time = jittered_start
        window.end_time = jittered_end
        window.jitter_minutes = jitter_minutes
        window.reasoning = f"Optimal window with gaussian jitter ({jitter_minutes:+.1f} min)"
        
        logger.debug(f"Applied jitter: {jitter_minutes:+.1f} minutes")
        return window
    
    def _apply_extra_jitter(self, window: TimingWindow, account: AccountProfile) -> TimingWindow:
        """Aplica jitter extra para romper patterns"""
        
        # Jitter más agresivo
        extra_jitter = self._rng.uniform(-30, 30)  # ±30 min uniform
        
        window.start_time += timedelta(minutes=extra_jitter)
        window.end_time += timedelta(minutes=extra_jitter)
        window.jitter_minutes += extra_jitter
        window.reasoning += f" + extra jitter ({extra_jitter:+.1f} min)"
        
        return window
    
    # ========================================================================
    # PATTERN CHECKS
    # ========================================================================
    
    def _check_pattern_similarity(self, window: TimingWindow, account: AccountProfile) -> bool:
        """Verifica si el window tiene pattern similarity con posts recientes"""
        
        if not account.last_post_at:
            return False
        
        # Check gap con último post
        gap_hours = (window.start_time - account.last_post_at).total_seconds() / 3600
        
        # Si el gap es muy consistente con gaps anteriores → pattern
        # TODO: Implementar análisis estadístico real con múltiples posts
        
        # Por ahora: simple check de gap exacto
        if abs(gap_hours - 24.0) < 0.5:  # Exactamente 24h ±30min
            logger.warning(f"Pattern detected: gap={gap_hours:.2f}h (too close to 24h)")
            return True
        
        return False
    
    def _too_close_to_existing(self, new_time: datetime, existing_times: List[datetime]) -> bool:
        """Check si new_time está demasiado cerca de existing times"""
        
        for existing in existing_times:
            gap_hours = abs((new_time - existing).total_seconds() / 3600)
            if gap_hours < self.config.min_time_gap_hours:
                return True
        
        return False
    
    def _respects_warmup_constraints(self, window_time: datetime, account: AccountProfile) -> bool:
        """Verifica que el window respete warmup constraints"""
        
        if not account.last_post_at:
            return True  # Primer post, OK
        
        # Check gap mínimo
        gap_hours = (window_time - account.last_post_at).total_seconds() / 3600
        
        if gap_hours < self.config.warmup_min_gap_hours:
            logger.debug(f"Warmup constraint violated: gap={gap_hours:.1f}h < {self.config.warmup_min_gap_hours}h")
            return False
        
        return True


# ============================================================================
# STATISTICAL HELPERS
# ============================================================================

def calculate_time_series_entropy(timestamps: List[datetime]) -> float:
    """
    Calcula entropía de una serie temporal de timestamps.
    
    Mayor entropía = más random = menos patrón.
    """
    if len(timestamps) < 2:
        return 0.0
    
    # Discretize a bins de 1 hora
    hours = [(ts.hour + ts.minute / 60.0) for ts in timestamps]
    
    # Histogram
    bins = [0] * 24
    for hour in hours:
        bin_idx = int(hour) % 24
        bins[bin_idx] += 1
    
    # Shannon entropy
    total = len(hours)
    entropy = 0.0
    
    for count in bins:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    # Normalize a [0, 1]
    max_entropy = math.log2(24)  # Uniform distribution
    return entropy / max_entropy


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def find_next_optimal_time(
    account_id: str,
    niche_id: str = "music",
    hours_ahead: int = 24
) -> datetime:
    """Helper para encontrar próximo timing óptimo simple"""
    
    optimizer = TimingOptimizer()
    
    # Mock account
    account = AccountProfile(
        account_id=account_id,
        niche_id=niche_id,
        niche_name=niche_id.title(),
        is_active=True,
        optimal_hours=[10, 14, 18, 21],
        last_post_at=datetime.now() - timedelta(hours=25),
    )
    
    window = optimizer.find_optimal_window(account, datetime.now(), hours_ahead)
    return window.start_time


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "TimingConfig",
    "TimingOptimizer",
    "calculate_time_series_entropy",
    "find_next_optimal_time",
]
