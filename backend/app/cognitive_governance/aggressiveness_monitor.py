"""
SPRINT 14 - Aggressiveness Monitor (Monitor Global de Agresividad)

Objetivo:
Medir la agresividad GLOBAL del sistema y evitar comportamientos detectables por plataformas.

Score:
{
  "global_aggressiveness_score": 0.64,
  "safe_zone": "<0.7",
  "warning_zone": "0.7–0.85",
  "danger_zone": ">0.85"
}

Reglas:
- Si score > 0.85 → bloquear acciones críticas
- Si 0.70–0.85 → espaciar publicaciones, reducir intensidad
- Si < 0.70 → operar con normalidad

Integración:
- Orchestrator (autorregulación)
- Risk Simulation (ajuste de umbral)
- Supervisor Global (alertas)
- Decision Ledger (registro)

Factores de agresividad:
- Velocidad de acciones
- Concentración temporal
- Repetición de patrones
- Actividad de múltiples cuentas
- Volumen vs baseline
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import statistics


class AggressivenessLevel(Enum):
    """Niveles de agresividad del sistema"""
    SAFE = "safe"  # < 0.7
    WARNING = "warning"  # 0.7 - 0.85
    DANGER = "danger"  # > 0.85


@dataclass
class AggressivenessScore:
    """
    Score de agresividad global del sistema
    """
    timestamp: datetime
    global_score: float  # 0.0 - 1.0
    level: AggressivenessLevel
    
    # Componentes del score
    velocity_score: float  # Velocidad de acciones
    concentration_score: float  # Concentración temporal
    pattern_repetition_score: float  # Repetición de patrones
    multi_account_score: float  # Actividad multi-cuenta
    volume_vs_baseline_score: float  # Volumen vs baseline
    
    # Recomendaciones
    should_throttle: bool
    should_block_critical: bool
    cooldown_recommended_minutes: int = 0
    
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        return f"Aggressiveness: {self.level.value.upper()} ({self.global_score:.2f}) | " \
               f"Velocity: {self.velocity_score:.2f} | " \
               f"Concentration: {self.concentration_score:.2f} | " \
               f"Pattern: {self.pattern_repetition_score:.2f}"
    
    def is_safe_to_operate(self) -> bool:
        """Check if system can operate normally"""
        return self.level == AggressivenessLevel.SAFE and not self.should_block_critical


class AggressivenessMonitor:
    """
    Monitor global de agresividad del sistema
    
    Características:
    - Monitoreo en tiempo real
    - Autorregulación automática
    - Integración con Orchestrator
    - Alertas proactivas
    - Cooldown automático
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Umbrales
        self.safe_threshold = self.config.get('safe_threshold', 0.7)
        self.warning_threshold = self.config.get('warning_threshold', 0.85)
        
        # Ventanas de tiempo para análisis
        self.window_5min = deque(maxlen=300)  # 5 minutos (1 evento/segundo max)
        self.window_1hour = deque(maxlen=3600)  # 1 hora
        self.window_24hours = deque(maxlen=86400)  # 24 horas
        
        # Baseline (actividad normal)
        self.baseline_actions_per_hour = self.config.get('baseline_actions_per_hour', 10)
        self.baseline_accounts_active = self.config.get('baseline_accounts_active', 3)
        
        # Histórico de scores
        self._score_history: List[AggressivenessScore] = []
        self._history_limit = 1000
        
        # Estadísticas
        self.total_evaluations = 0
        self.throttle_events = 0
        self.block_events = 0
        
        # Estado actual
        self.current_score: Optional[AggressivenessScore] = None
        self.cooldown_until: Optional[datetime] = None
    
    def record_action(
        self,
        action_type: str,
        account_id: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Registrar una acción del sistema
        
        Esto alimenta el monitor para calcular agresividad
        """
        timestamp = timestamp or datetime.now()
        
        action_data = {
            'type': action_type,
            'account_id': account_id,
            'timestamp': timestamp
        }
        
        # Agregar a ventanas
        self.window_5min.append(action_data)
        self.window_1hour.append(action_data)
        self.window_24hours.append(action_data)
    
    def evaluate_aggressiveness(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> AggressivenessScore:
        """
        Evaluar agresividad global del sistema
        
        Returns:
            AggressivenessScore con nivel y recomendaciones
        """
        context = context or {}
        now = datetime.now()
        
        # Limpiar ventanas (remover eventos antiguos)
        self._cleanup_windows(now)
        
        # 1. Velocity Score (velocidad de acciones)
        velocity_score = self._calculate_velocity_score()
        
        # 2. Concentration Score (concentración temporal)
        concentration_score = self._calculate_concentration_score()
        
        # 3. Pattern Repetition Score
        pattern_score = self._calculate_pattern_repetition_score()
        
        # 4. Multi-Account Score
        multi_account_score = self._calculate_multi_account_score()
        
        # 5. Volume vs Baseline Score
        volume_score = self._calculate_volume_vs_baseline_score()
        
        # Calcular score global (ponderado)
        global_score = (
            velocity_score * 0.25 +
            concentration_score * 0.20 +
            pattern_score * 0.25 +
            multi_account_score * 0.15 +
            volume_score * 0.15
        )
        
        # Determinar nivel
        if global_score < self.safe_threshold:
            level = AggressivenessLevel.SAFE
        elif global_score < self.warning_threshold:
            level = AggressivenessLevel.WARNING
        else:
            level = AggressivenessLevel.DANGER
        
        # Generar recomendaciones
        recommendations = []
        warnings = []
        should_throttle = False
        should_block_critical = False
        cooldown_minutes = 0
        
        if level == AggressivenessLevel.WARNING:
            should_throttle = True
            recommendations.append("Space out actions by 30-60 seconds")
            recommendations.append("Reduce concurrent account activity")
            warnings.append(f"Approaching danger zone: {global_score:.2f}")
        
        if level == AggressivenessLevel.DANGER:
            should_throttle = True
            should_block_critical = True
            cooldown_minutes = self._calculate_cooldown_minutes(global_score)
            recommendations.append(f"COOLDOWN: Wait {cooldown_minutes} minutes")
            recommendations.append("Block all critical actions")
            recommendations.append("Allow only safe actions")
            warnings.append(f"DANGER ZONE: {global_score:.2f} - System too aggressive")
        
        # Recomendaciones específicas por componente alto
        if velocity_score > 0.7:
            recommendations.append("Slow down action velocity")
        if concentration_score > 0.7:
            recommendations.append("Distribute actions over longer time window")
        if pattern_score > 0.7:
            recommendations.append("Add more randomness to patterns")
        if multi_account_score > 0.7:
            recommendations.append("Reduce number of concurrent active accounts")
        if volume_score > 0.7:
            recommendations.append("Reduce total action volume")
        
        score = AggressivenessScore(
            timestamp=now,
            global_score=global_score,
            level=level,
            velocity_score=velocity_score,
            concentration_score=concentration_score,
            pattern_repetition_score=pattern_score,
            multi_account_score=multi_account_score,
            volume_vs_baseline_score=volume_score,
            should_throttle=should_throttle,
            should_block_critical=should_block_critical,
            cooldown_recommended_minutes=cooldown_minutes,
            recommendations=recommendations,
            warnings=warnings
        )
        
        # Registrar score
        self._score_history.append(score)
        if len(self._score_history) > self._history_limit:
            self._score_history.pop(0)
        
        self.current_score = score
        self.total_evaluations += 1
        
        if should_throttle:
            self.throttle_events += 1
        if should_block_critical:
            self.block_events += 1
            self.cooldown_until = now + timedelta(minutes=cooldown_minutes)
        
        return score
    
    def is_in_cooldown(self) -> bool:
        """Check if system is in cooldown period"""
        if self.cooldown_until is None:
            return False
        return datetime.now() < self.cooldown_until
    
    def can_execute_action(self, action_criticality: str = "standard") -> bool:
        """
        Check if an action can be executed given current aggressiveness
        
        Args:
            action_criticality: "micro", "standard", "critical", "structural"
        
        Returns:
            bool: True if action can proceed
        """
        if self.is_in_cooldown():
            return False
        
        if self.current_score is None:
            return True  # No evaluation yet, allow
        
        if action_criticality in ["critical", "structural"]:
            return not self.current_score.should_block_critical
        
        if action_criticality == "standard":
            return self.current_score.level != AggressivenessLevel.DANGER
        
        # MICRO actions always allowed unless in cooldown
        return True
    
    def _calculate_velocity_score(self) -> float:
        """
        Calcular score de velocidad de acciones
        
        Métricas:
        - Acciones en últimos 5 minutos
        - Tasa de cambio
        - Picos de actividad
        """
        if not self.window_5min:
            return 0.0
        
        actions_5min = len(self.window_5min)
        
        # Baseline: ~10 acciones/5min es normal (2/min)
        baseline_5min = (self.baseline_actions_per_hour / 60) * 5
        
        ratio = actions_5min / max(baseline_5min, 1)
        
        # Convertir a score 0-1
        # ratio 1.0 = baseline = score 0.3
        # ratio 2.0 = 2x baseline = score 0.6
        # ratio 3.0+ = 3x+ baseline = score 0.9+
        score = min(ratio / 3.0, 1.0) * 0.9
        
        return min(score, 1.0)
    
    def _calculate_concentration_score(self) -> float:
        """
        Calcular score de concentración temporal
        
        Métricas:
        - Desviación estándar de intervalos
        - Clustering temporal
        - Bursts de actividad
        """
        if len(self.window_1hour) < 3:
            return 0.0
        
        # Calcular intervalos entre acciones
        timestamps = [a['timestamp'] for a in self.window_1hour]
        timestamps.sort()
        
        intervals = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(delta)
        
        if not intervals:
            return 0.0
        
        # Calcular coeficiente de variación
        try:
            mean_interval = statistics.mean(intervals)
            stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
            cv = stdev_interval / mean_interval if mean_interval > 0 else 0
            
            # Bajo CV = alta concentración (mecánico)
            # Alto CV = baja concentración (natural)
            # Invertimos: score alto = concentrado
            score = max(0, 1.0 - min(cv / 2.0, 1.0))
            
            return score
        except:
            return 0.5
    
    def _calculate_pattern_repetition_score(self) -> float:
        """
        Calcular score de repetición de patrones
        
        Métricas:
        - Tipos de acciones repetidas
        - Secuencias idénticas
        - Predictibilidad
        """
        if len(self.window_1hour) < 5:
            return 0.0
        
        action_types = [a['type'] for a in self.window_1hour]
        
        # Calcular entropía (diversidad)
        type_counts = defaultdict(int)
        for t in action_types:
            type_counts[t] += 1
        
        total = len(action_types)
        entropy = 0.0
        for count in type_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * (p ** 0.5)  # Simplified entropy
        
        # Normalizar entropy (0-1)
        # Baja entropía = alta repetición
        max_entropy = 1.0  # Teórico máximo
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Invertir: score alto = baja entropía (mucha repetición)
        score = 1.0 - min(normalized_entropy, 1.0)
        
        return score
    
    def _calculate_multi_account_score(self) -> float:
        """
        Calcular score de actividad multi-cuenta
        
        Métricas:
        - Número de cuentas activas simultáneamente
        - Correlación de timing
        - Cuentas vs baseline
        """
        if not self.window_1hour:
            return 0.0
        
        # Contar cuentas únicas activas en última hora
        account_ids = set(a['account_id'] for a in self.window_1hour)
        active_accounts = len(account_ids)
        
        # Ratio vs baseline
        ratio = active_accounts / max(self.baseline_accounts_active, 1)
        
        # Convertir a score
        # 1x baseline = 0.3
        # 2x baseline = 0.6
        # 3x+ baseline = 0.9+
        score = min(ratio / 3.0, 1.0) * 0.9
        
        return min(score, 1.0)
    
    def _calculate_volume_vs_baseline_score(self) -> float:
        """
        Calcular score de volumen vs baseline
        
        Métricas:
        - Acciones totales en 24h
        - Comparación con baseline histórico
        - Desviación vs promedio
        """
        if not self.window_24hours:
            return 0.0
        
        actions_24h = len(self.window_24hours)
        baseline_24h = self.baseline_actions_per_hour * 24
        
        ratio = actions_24h / max(baseline_24h, 1)
        
        # Score similar a velocity
        score = min(ratio / 3.0, 1.0) * 0.9
        
        return min(score, 1.0)
    
    def _calculate_cooldown_minutes(self, global_score: float) -> int:
        """
        Calcular minutos de cooldown recomendados
        
        Basado en qué tan alto es el score
        """
        if global_score < 0.85:
            return 0
        elif global_score < 0.90:
            return 15
        elif global_score < 0.95:
            return 30
        else:
            return 60
    
    def _cleanup_windows(self, now: datetime):
        """Limpiar ventanas de tiempo (remover eventos antiguos)"""
        cutoff_5min = now - timedelta(minutes=5)
        cutoff_1hour = now - timedelta(hours=1)
        cutoff_24hours = now - timedelta(hours=24)
        
        # Las deques con maxlen se autolimpian, pero filtramos por timestamp
        # para mayor precisión
        self.window_5min = deque(
            (a for a in self.window_5min if a['timestamp'] >= cutoff_5min),
            maxlen=300
        )
        self.window_1hour = deque(
            (a for a in self.window_1hour if a['timestamp'] >= cutoff_1hour),
            maxlen=3600
        )
        self.window_24hours = deque(
            (a for a in self.window_24hours if a['timestamp'] >= cutoff_24hours),
            maxlen=86400
        )
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current aggressiveness status"""
        if self.current_score is None:
            return {
                'status': 'not_evaluated',
                'in_cooldown': self.is_in_cooldown()
            }
        
        return {
            'status': 'evaluated',
            'global_score': self.current_score.global_score,
            'level': self.current_score.level.value,
            'should_throttle': self.current_score.should_throttle,
            'should_block_critical': self.current_score.should_block_critical,
            'in_cooldown': self.is_in_cooldown(),
            'cooldown_until': self.cooldown_until.isoformat() if self.cooldown_until else None,
            'recommendations': self.current_score.recommendations,
            'warnings': self.current_score.warnings,
            'components': {
                'velocity': self.current_score.velocity_score,
                'concentration': self.current_score.concentration_score,
                'pattern': self.current_score.pattern_repetition_score,
                'multi_account': self.current_score.multi_account_score,
                'volume': self.current_score.volume_vs_baseline_score
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        return {
            'total_evaluations': self.total_evaluations,
            'throttle_events': self.throttle_events,
            'block_events': self.block_events,
            'throttle_rate': self.throttle_events / self.total_evaluations if self.total_evaluations > 0 else 0,
            'block_rate': self.block_events / self.total_evaluations if self.total_evaluations > 0 else 0,
            'window_sizes': {
                '5min': len(self.window_5min),
                '1hour': len(self.window_1hour),
                '24hours': len(self.window_24hours)
            },
            'in_cooldown': self.is_in_cooldown()
        }
    
    def get_score_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent score history"""
        recent = self._score_history[-limit:]
        return [
            {
                'timestamp': s.timestamp.isoformat(),
                'global_score': s.global_score,
                'level': s.level.value,
                'should_throttle': s.should_throttle
            }
            for s in recent
        ]
