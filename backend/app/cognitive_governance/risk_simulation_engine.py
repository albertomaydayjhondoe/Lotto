"""
SPRINT 14 - Risk Simulation Engine (Simulación de Riesgo Previa Ligera)

Objetivo:
Simular el impacto y riesgo de una acción ANTES de que el Orchestrator decida ejecutarla.

Funciones:
- simulate_action(action_type, context)
- estimate_identity_risk()
- estimate_pattern_repetition()
- estimate_shadowban_probability()
- estimate_expected_engagement()

Ejemplo output:
{
  "estimated_engagement": "+11%",
  "identity_risk": 0.27,
  "pattern_similarity": "medium",
  "shadowban_probability": 0.08
}

Se aplica solamente a:
- Escalados
- Activación de múltiples cuentas
- Acciones repetitivas
- Ventanas de sensibilidad
- Picos de actividad

Integración:
- Orchestrator: Consulta antes de ejecutar
- Aggressiveness Monitor: Ajusta umbral
- Decision Ledger: Registra simulación
- Supervisor Layer: Valida riesgo alto
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import statistics
from collections import defaultdict


class ActionType(Enum):
    """Tipos de acciones simulables"""
    # Content actions
    POST_CONTENT = "post_content"
    BOOST_CONTENT = "boost_content"
    SCHEDULE_CONTENT = "schedule_content"
    
    # Account actions
    ACTIVATE_ACCOUNT = "activate_account"
    SCALE_ACCOUNTS = "scale_accounts"
    WARMUP_ACTION = "warmup_action"
    
    # Engagement actions
    LIKE_BATCH = "like_batch"
    COMMENT_BATCH = "comment_batch"
    FOLLOW_BATCH = "follow_batch"
    
    # Risk actions
    IDENTITY_SWITCH = "identity_switch"
    PROXY_CHANGE = "proxy_change"
    PATTERN_REPEAT = "pattern_repeat"


class RiskLevel(Enum):
    """Niveles de riesgo simulado"""
    SAFE = "safe"  # < 0.3
    LOW = "low"  # 0.3 - 0.5
    MEDIUM = "medium"  # 0.5 - 0.7
    HIGH = "high"  # 0.7 - 0.85
    CRITICAL = "critical"  # > 0.85


@dataclass
class SimulationResult:
    """
    Resultado de una simulación de riesgo
    """
    action_type: ActionType
    timestamp: datetime
    
    # Métricas de riesgo
    identity_risk: float  # 0.0 - 1.0
    pattern_similarity: float  # 0.0 - 1.0 (parecido a acciones previas)
    shadowban_probability: float  # 0.0 - 1.0
    correlation_risk: float  # 0.0 - 1.0 (correlación entre cuentas)
    
    # Métricas de impacto esperado
    estimated_engagement: float  # -1.0 - +1.0 (cambio porcentual esperado)
    estimated_reach: float  # -1.0 - +1.0
    estimated_conversion: float  # -1.0 - +1.0
    
    # Score final
    total_risk_score: float  # 0.0 - 1.0
    risk_level: RiskLevel
    
    # Recomendaciones
    should_proceed: bool
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    
    # Context
    simulation_confidence: float = 0.7  # Confianza en la simulación
    factors_considered: List[str] = field(default_factory=list)
    
    def get_risk_summary(self) -> str:
        """Get human-readable risk summary"""
        return f"Risk: {self.risk_level.value.upper()} ({self.total_risk_score:.2f}) | " \
               f"Identity: {self.identity_risk:.2f} | " \
               f"Shadowban: {self.shadowban_probability:.2f} | " \
               f"Pattern: {self.pattern_similarity:.2f}"
    
    def is_safe_to_proceed(self) -> bool:
        """Check if action is safe to proceed"""
        return self.should_proceed and len(self.blockers) == 0


class RiskSimulationEngine:
    """
    Motor de simulación de riesgo ligero y rápido
    
    Características:
    - Simulación < 500ms
    - No requiere LLM (solo para validación crítica)
    - Basado en heurísticas + histórico
    - Integrado con Account BirthFlow (Sprint 12)
    - Integrado con Satellite Intelligence (Sprint 11)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Umbrales de riesgo
        self.risk_thresholds = {
            'identity_risk': self.config.get('identity_risk_threshold', 0.4),
            'pattern_similarity': self.config.get('pattern_threshold', 0.6),
            'shadowban_probability': self.config.get('shadowban_threshold', 0.3),
            'correlation_risk': self.config.get('correlation_threshold', 0.5),
        }
        
        # Histórico de acciones (últimas 1000)
        self._action_history: List[Dict[str, Any]] = []
        self._history_limit = 1000
        
        # Estadísticas
        self.simulations_run = 0
        self.simulations_blocked = 0
        self.avg_simulation_time_ms = 0
    
    def simulate_action(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> SimulationResult:
        """
        Simular una acción antes de ejecutarla
        
        Args:
            action_type: Tipo de acción a simular
            context: Contexto completo {
                'account_id': str,
                'platform': str,
                'content_id': Optional[str],
                'target_accounts': Optional[List[str]],
                'timestamp': datetime,
                'recent_actions': List[Dict],
                'account_state': str,
                'metrics': Dict,
                ...
            }
        
        Returns:
            SimulationResult con riesgo estimado y recomendaciones
        """
        start_time = datetime.now()
        
        # Extraer información del contexto
        account_id = context.get('account_id', 'unknown')
        platform = context.get('platform', 'unknown')
        recent_actions = context.get('recent_actions', [])
        account_state = context.get('account_state', 'unknown')
        metrics = context.get('metrics', {})
        
        # 1. Estimar riesgo de identidad
        identity_risk = self._estimate_identity_risk(context)
        
        # 2. Estimar similitud de patrones
        pattern_similarity = self._estimate_pattern_similarity(action_type, recent_actions)
        
        # 3. Estimar probabilidad de shadowban
        shadowban_prob = self._estimate_shadowban_probability(context, metrics)
        
        # 4. Estimar riesgo de correlación
        correlation_risk = self._estimate_correlation_risk(context)
        
        # 5. Estimar impacto en engagement
        estimated_engagement = self._estimate_engagement_impact(action_type, context)
        estimated_reach = self._estimate_reach_impact(action_type, context)
        estimated_conversion = self._estimate_conversion_impact(action_type, context)
        
        # Calcular score total de riesgo (ponderado)
        total_risk_score = (
            identity_risk * 0.25 +
            pattern_similarity * 0.25 +
            shadowban_prob * 0.30 +
            correlation_risk * 0.20
        )
        
        # Determinar nivel de riesgo
        if total_risk_score < 0.3:
            risk_level = RiskLevel.SAFE
        elif total_risk_score < 0.5:
            risk_level = RiskLevel.LOW
        elif total_risk_score < 0.7:
            risk_level = RiskLevel.MEDIUM
        elif total_risk_score < 0.85:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        # Generar recomendaciones
        recommendations = []
        warnings = []
        blockers = []
        
        if identity_risk > self.risk_thresholds['identity_risk']:
            warnings.append(f"Identity risk elevated: {identity_risk:.2f}")
            if identity_risk > 0.7:
                recommendations.append("Consider rotating fingerprints")
        
        if pattern_similarity > self.risk_thresholds['pattern_similarity']:
            warnings.append(f"Pattern similarity high: {pattern_similarity:.2f}")
            recommendations.append("Add randomness to timing/content")
        
        if shadowban_prob > self.risk_thresholds['shadowban_probability']:
            warnings.append(f"Shadowban risk: {shadowban_prob:.2f}")
            if shadowban_prob > 0.5:
                blockers.append("Shadowban probability too high - HOLD")
                recommendations.append("Wait 24-48h before retrying")
        
        if correlation_risk > self.risk_thresholds['correlation_risk']:
            warnings.append(f"Correlation risk: {correlation_risk:.2f}")
            recommendations.append("Space out actions across accounts")
        
        # Decisión: proceder o no
        should_proceed = (
            total_risk_score < 0.75 and
            len(blockers) == 0 and
            shadowban_prob < 0.6
        )
        
        if not should_proceed and len(blockers) == 0:
            blockers.append(f"Total risk too high: {total_risk_score:.2f}")
        
        # Factores considerados
        factors_considered = [
            "identity_stability",
            "pattern_analysis",
            "shadowban_signals",
            "account_correlation",
            "historical_performance"
        ]
        
        # Registrar en histórico
        self._action_history.append({
            'action_type': action_type.value,
            'timestamp': datetime.now(),
            'risk_score': total_risk_score,
            'account_id': account_id,
            'platform': platform
        })
        if len(self._action_history) > self._history_limit:
            self._action_history.pop(0)
        
        # Actualizar estadísticas
        self.simulations_run += 1
        if not should_proceed:
            self.simulations_blocked += 1
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.avg_simulation_time_ms = (
            (self.avg_simulation_time_ms * (self.simulations_run - 1) + elapsed_ms) 
            / self.simulations_run
        )
        
        return SimulationResult(
            action_type=action_type,
            timestamp=datetime.now(),
            identity_risk=identity_risk,
            pattern_similarity=pattern_similarity,
            shadowban_probability=shadowban_prob,
            correlation_risk=correlation_risk,
            estimated_engagement=estimated_engagement,
            estimated_reach=estimated_reach,
            estimated_conversion=estimated_conversion,
            total_risk_score=total_risk_score,
            risk_level=risk_level,
            should_proceed=should_proceed,
            recommendations=recommendations,
            warnings=warnings,
            blockers=blockers,
            factors_considered=factors_considered
        )
    
    def _estimate_identity_risk(self, context: Dict[str, Any]) -> float:
        """
        Estimar riesgo de identidad digital
        
        Factores:
        - Estabilidad de fingerprint
        - Cambios recientes de proxy/IP
        - Consistencia de user-agent
        - Historial de cambios
        """
        risk = 0.0
        
        # Fingerprint changes
        fingerprint_changes = context.get('fingerprint_changes_24h', 0)
        if fingerprint_changes > 0:
            risk += min(fingerprint_changes * 0.15, 0.4)
        
        # IP/Proxy changes
        ip_changes = context.get('ip_changes_24h', 0)
        if ip_changes > 0:
            risk += min(ip_changes * 0.20, 0.5)
        
        # User-agent inconsistency
        ua_inconsistent = context.get('user_agent_inconsistent', False)
        if ua_inconsistent:
            risk += 0.25
        
        # Account age (nuevas cuentas = más riesgo)
        account_age_days = context.get('account_age_days', 0)
        if account_age_days < 7:
            risk += 0.20
        elif account_age_days < 30:
            risk += 0.10
        
        return min(risk, 1.0)
    
    def _estimate_pattern_similarity(
        self,
        action_type: ActionType,
        recent_actions: List[Dict[str, Any]]
    ) -> float:
        """
        Estimar similitud con patrones previos
        
        Factores:
        - Repetición de timing
        - Repetición de contenido
        - Repetición de targets
        - Intervalos mecánicos
        """
        if not recent_actions:
            return 0.0
        
        similarity = 0.0
        
        # Check for repeated action types
        action_types = [a.get('type') for a in recent_actions]
        if action_types.count(action_type.value) > len(action_types) * 0.5:
            similarity += 0.30
        
        # Check for mechanical timing (intervalos idénticos)
        timestamps = [a.get('timestamp') for a in recent_actions if a.get('timestamp')]
        if len(timestamps) >= 3:
            intervals = []
            for i in range(1, len(timestamps)):
                if isinstance(timestamps[i], datetime) and isinstance(timestamps[i-1], datetime):
                    delta = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(delta)
            
            if intervals:
                # Calcular varianza
                try:
                    variance = statistics.variance(intervals) if len(intervals) > 1 else 0
                    mean_interval = statistics.mean(intervals)
                    cv = (variance ** 0.5) / mean_interval if mean_interval > 0 else 0
                    
                    # Baja varianza = mecánico
                    if cv < 0.15:
                        similarity += 0.40
                    elif cv < 0.30:
                        similarity += 0.20
                except:
                    pass
        
        # Check for repeated targets/content
        targets = [a.get('target') for a in recent_actions if a.get('target')]
        if targets:
            unique_ratio = len(set(targets)) / len(targets)
            if unique_ratio < 0.3:  # Muchas repeticiones
                similarity += 0.30
        
        return min(similarity, 1.0)
    
    def _estimate_shadowban_probability(
        self,
        context: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> float:
        """
        Estimar probabilidad de shadowban
        
        Señales:
        - Caída súbita de reach
        - Engagement rate bajo
        - Contenido reportado
        - Violaciones de policy
        - Patrones detectables
        """
        probability = 0.0
        
        # Caída de reach
        reach_drop = metrics.get('reach_drop_7d', 0.0)  # Porcentaje
        if reach_drop > 0.30:
            probability += 0.40
        elif reach_drop > 0.15:
            probability += 0.20
        
        # Engagement rate bajo
        engagement_rate = metrics.get('engagement_rate', 0.05)
        if engagement_rate < 0.01:
            probability += 0.30
        elif engagement_rate < 0.02:
            probability += 0.15
        
        # Contenido reportado recientemente
        reports_7d = context.get('reports_7d', 0)
        if reports_7d > 0:
            probability += min(reports_7d * 0.25, 0.50)
        
        # Violaciones de policy
        policy_violations = context.get('policy_violations_30d', 0)
        if policy_violations > 0:
            probability += min(policy_violations * 0.20, 0.40)
        
        # Señales de shadowban conocidas
        shadowban_signals = context.get('shadowban_signals', [])
        if shadowban_signals:
            probability += min(len(shadowban_signals) * 0.15, 0.50)
        
        return min(probability, 1.0)
    
    def _estimate_correlation_risk(self, context: Dict[str, Any]) -> float:
        """
        Estimar riesgo de correlación entre cuentas
        
        Factores:
        - Cuentas operando simultáneamente
        - IP compartidas
        - Contenido similar
        - Timing coordinado
        """
        risk = 0.0
        
        # Cuentas activas simultáneamente
        concurrent_accounts = context.get('concurrent_accounts', 1)
        if concurrent_accounts > 5:
            risk += 0.30
        elif concurrent_accounts > 3:
            risk += 0.15
        
        # IP compartidas
        shared_ips = context.get('accounts_sharing_ip', 0)
        if shared_ips > 2:
            risk += min(shared_ips * 0.10, 0.40)
        
        # Contenido similar entre cuentas
        content_similarity = context.get('content_similarity_score', 0.0)  # 0-1
        if content_similarity > 0.7:
            risk += 0.35
        elif content_similarity > 0.5:
            risk += 0.20
        
        # Timing coordinado (acciones en <5min)
        timing_correlation = context.get('timing_correlation', 0.0)  # 0-1
        if timing_correlation > 0.8:
            risk += 0.30
        elif timing_correlation > 0.6:
            risk += 0.15
        
        return min(risk, 1.0)
    
    def _estimate_engagement_impact(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> float:
        """
        Estimar impacto en engagement (-1.0 a +1.0)
        """
        # Base impact por tipo de acción
        base_impacts = {
            ActionType.POST_CONTENT: 0.05,
            ActionType.BOOST_CONTENT: 0.15,
            ActionType.SCHEDULE_CONTENT: 0.03,
            ActionType.ACTIVATE_ACCOUNT: 0.10,
            ActionType.SCALE_ACCOUNTS: 0.20,
            ActionType.WARMUP_ACTION: 0.02,
            ActionType.LIKE_BATCH: 0.08,
            ActionType.COMMENT_BATCH: 0.12,
            ActionType.FOLLOW_BATCH: 0.10,
        }
        
        base = base_impacts.get(action_type, 0.0)
        
        # Ajustar por contexto
        content_quality = context.get('content_quality_score', 0.5)  # 0-1
        timing_score = context.get('timing_score', 0.5)  # 0-1
        audience_match = context.get('audience_match_score', 0.5)  # 0-1
        
        multiplier = (content_quality + timing_score + audience_match) / 3
        
        return base * multiplier
    
    def _estimate_reach_impact(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> float:
        """Estimar impacto en reach"""
        # Similar a engagement pero con diferentes pesos
        base = self._estimate_engagement_impact(action_type, context)
        return base * 0.8  # Reach generalmente menor que engagement
    
    def _estimate_conversion_impact(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> float:
        """Estimar impacto en conversión"""
        # Conversión es más difícil que engagement
        base = self._estimate_engagement_impact(action_type, context)
        conversion_funnel_strength = context.get('conversion_funnel_strength', 0.3)
        return base * conversion_funnel_strength
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation engine statistics"""
        return {
            'simulations_run': self.simulations_run,
            'simulations_blocked': self.simulations_blocked,
            'block_rate': self.simulations_blocked / self.simulations_run if self.simulations_run > 0 else 0,
            'avg_simulation_time_ms': round(self.avg_simulation_time_ms, 2),
            'history_size': len(self._action_history)
        }
