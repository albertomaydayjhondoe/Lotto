"""
SPRINT 14 - Cognitive Governance Bridge

Capa de integración entre el Orchestrator y Cognitive Governance Layer.

Propósito:
- Punto de entrada único para todas las consultas de gobernanza
- Workflow completo: clasificación → simulación → validación → registro
- Autorregulación automática
- Bloqueo de acciones peligrosas
- Narrativa humana automática

Flujo típico:
1. Orchestrator quiere tomar decisión X
2. Orchestrator llama: bridge.evaluate_decision(...)
3. Bridge:
   a. Clasifica (MICRO/STANDARD/CRITICAL/STRUCTURAL)
   b. Si CRITICAL+: Simula riesgo
   c. Si agresividad alta: Bloquea
   d. Si todo OK: Registra en ledger
   e. Retorna: aprobado/rechazado + narrativa
4. Orchestrator ejecuta (si aprobado)
5. Orchestrator llama: bridge.record_execution(...)

Integración:
- Decision Classifier (clasificación)
- Risk Simulation Engine (simulación)
- Aggressiveness Monitor (autorregulación)
- Decision Ledger (registro)
- Narrative Observability (explicación)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from .decision_classifier import DecisionClassifier, DecisionLevel
from .risk_simulation_engine import RiskSimulationEngine, ActionType
from .aggressiveness_monitor import AggressivenessMonitor, AggressivenessLevel
from .decision_ledger import DecisionLedger, DecisionType, DecisionRecord
from .narrative_observability import NarrativeObservability


class DecisionOutcome(Enum):
    """Resultado de evaluación de decisión"""
    APPROVED = "approved"  # Decisión aprobada
    REJECTED = "rejected"  # Decisión rechazada
    REQUIRES_HUMAN = "requires_human"  # Requiere aprobación humana
    REQUIRES_LLM = "requires_llm"  # Requiere validación LLM
    THROTTLED = "throttled"  # Rechazada por throttling


@dataclass
class GovernanceEvaluation:
    """
    Resultado completo de evaluación de gobernanza
    """
    outcome: DecisionOutcome
    classification_level: DecisionLevel
    
    # Flags
    approved: bool
    requires_simulation: bool
    requires_llm_validation: bool
    requires_human_approval: bool
    
    # Scores
    risk_score: float
    confidence_score: float
    aggressiveness_score: float
    
    # Recomendaciones y explicación
    recommendations: List[str]
    warnings: List[str]
    blockers: List[str]
    narrative_explanation: str
    
    # IDs para tracking
    decision_id: Optional[str] = None
    simulation_id: Optional[str] = None
    
    # Metadata
    evaluation_time_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        return f"Outcome: {self.outcome.value.upper()} | " \
               f"Level: {self.classification_level.value} | " \
               f"Risk: {self.risk_score:.2f} | " \
               f"Approved: {self.approved}"


class CognitiveGovernanceBridge:
    """
    Puente de integración entre Orchestrator y Cognitive Governance
    
    Responsabilidades:
    - Evaluar todas las decisiones del Orchestrator
    - Aplicar reglas de gobernanza automáticamente
    - Bloquear acciones peligrosas
    - Registrar decisiones en ledger
    - Generar narrativas humanas
    - Autorregular agresividad
    
    Uso desde Orchestrator:
    
    ```python
    bridge = CognitiveGovernanceBridge()
    
    # Antes de tomar decisión
    evaluation = bridge.evaluate_decision(
        decision_type="content_boost",
        context={...}
    )
    
    if evaluation.approved:
        # Ejecutar acción
        result = execute_action(...)
        
        # Registrar resultado
        bridge.record_execution(
            decision_id=evaluation.decision_id,
            success=result.success
        )
    else:
        # Decisión rechazada
        logger.warning(f"Decision blocked: {evaluation.blockers}")
    ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Inicializar componentes
        self.classifier = DecisionClassifier(self.config.get('classifier', {}))
        self.risk_engine = RiskSimulationEngine(self.config.get('risk_engine', {}))
        self.agg_monitor = AggressivenessMonitor(self.config.get('agg_monitor', {}))
        self.ledger = DecisionLedger(self.config.get('ledger', {}).get('storage_path', './storage/cognitive_governance'))
        self.narrative = NarrativeObservability(self.config.get('narrative', {}))
        
        # Configuración
        self.auto_block_critical = self.config.get('auto_block_critical', False)
        self.require_llm_for_critical = self.config.get('require_llm_for_critical', True)
        
        # Estadísticas
        self.total_evaluations = 0
        self.approvals = 0
        self.rejections = 0
        self.human_escalations = 0
    
    def evaluate_decision(
        self,
        decision_type: str,
        actor: str,
        context: Dict[str, Any],
        alternatives: Optional[List[str]] = None,
        chosen: Optional[str] = None,
        reasoning: Optional[List[str]] = None
    ) -> GovernanceEvaluation:
        """
        Evaluar una decisión antes de ejecutarla
        
        Args:
            decision_type: Tipo de decisión ("content_boost", "account_activation", etc.)
            actor: Quién toma la decisión ("Orchestrator", "Human", etc.)
            context: Contexto completo de la decisión
            alternatives: Alternativas consideradas
            chosen: Opción elegida
            reasoning: Razones de la elección
        
        Returns:
            GovernanceEvaluation con aprobación/rechazo + explicación
        """
        start_time = datetime.now()
        self.total_evaluations += 1
        
        # Valores por defecto
        alternatives = alternatives or []
        chosen = chosen or decision_type
        reasoning = reasoning or []
        
        # 1. Check aggressiveness first (fast fail)
        agg_score = self.agg_monitor.evaluate_aggressiveness(context)
        
        if agg_score.should_block_critical:
            self.rejections += 1
            return GovernanceEvaluation(
                outcome=DecisionOutcome.THROTTLED,
                classification_level=DecisionLevel.CRITICAL,  # Assumed
                approved=False,
                requires_simulation=False,
                requires_llm_validation=False,
                requires_human_approval=False,
                risk_score=agg_score.global_score,
                confidence_score=0.0,
                aggressiveness_score=agg_score.global_score,
                recommendations=agg_score.recommendations,
                warnings=agg_score.warnings,
                blockers=["System aggressiveness too high - throttled"],
                narrative_explanation=f"Decision blocked due to high system aggressiveness ({agg_score.global_score:.2f}). " +
                                     f"Cooldown required: {agg_score.cooldown_recommended_minutes} minutes.",
                evaluation_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
        
        # 2. Estimar riesgo e impacto (rápido, heurístico)
        estimated_risk = context.get('estimated_risk', 0.3)
        estimated_impact = context.get('estimated_impact', 0.2)
        
        # 3. Clasificar decisión
        classification = self.classifier.classify_decision(
            decision_type=decision_type,
            estimated_risk=estimated_risk,
            estimated_impact=estimated_impact,
            context=context
        )
        
        # 4. Si CRITICAL o STRUCTURAL: Simular
        simulation_result = None
        if classification.requires_simulation:
            # Map decision_type to ActionType
            action_type = self._map_decision_to_action(decision_type)
            simulation_result = self.risk_engine.simulate_action(action_type, context)
            
            # Update risk score with simulation
            estimated_risk = simulation_result.total_risk_score
        
        # 5. Determinar outcome
        outcome = DecisionOutcome.APPROVED
        approved = True
        blockers = []
        warnings = list(classification.risk_factors)
        recommendations = list(classification.reasoning)
        
        # Check blockers from simulation
        if simulation_result and not simulation_result.should_proceed:
            outcome = DecisionOutcome.REJECTED
            approved = False
            blockers.extend(simulation_result.blockers)
            warnings.extend(simulation_result.warnings)
            recommendations.extend(simulation_result.recommendations)
        
        # Check if requires human approval (STRUCTURAL)
        if classification.requires_human_approval:
            outcome = DecisionOutcome.REQUIRES_HUMAN
            approved = False  # Pending human approval
            self.human_escalations += 1
            blockers.append("Requires human approval (STRUCTURAL decision)")
        
        # Check if requires LLM validation (CRITICAL without simulation block)
        elif classification.requires_llm_validation and approved:
            if self.require_llm_for_critical:
                outcome = DecisionOutcome.REQUIRES_LLM
                # Still approved but flagged for LLM validation
                warnings.append("Requires LLM validation (Gemini 3.0)")
        
        # 6. Registrar en ledger (si STANDARD+)
        decision_id = None
        if classification.requires_ledger:
            decision_record = DecisionRecord(
                decision_id="",  # Will be generated
                actor=actor,
                decision_type=self._map_to_decision_type(decision_type),
                timestamp=datetime.now(),
                inputs=context.get('inputs', []),
                context=context,
                alternatives_considered=alternatives,
                chosen=chosen,
                reasoning=reasoning,
                confidence=context.get('confidence', 0.7),
                risk_score=estimated_risk,
                expected_impact=context.get('expected_impact'),
                validated_by=context.get('validated_by'),
                execution_status="pending"
            )
            decision_id = self.ledger.record_decision(decision_record)
        
        # 7. Generar narrativa explicativa
        narrative_explanation = self._generate_evaluation_narrative(
            decision_type,
            classification,
            simulation_result,
            agg_score,
            approved,
            blockers
        )
        
        # 8. Registrar acción en aggressiveness monitor
        if approved:
            self.agg_monitor.record_action(
                action_type=decision_type,
                account_id=context.get('account_id', 'system'),
                timestamp=datetime.now()
            )
        
        # Update stats
        if approved:
            self.approvals += 1
        else:
            self.rejections += 1
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return GovernanceEvaluation(
            outcome=outcome,
            classification_level=classification.level,
            approved=approved,
            requires_simulation=classification.requires_simulation,
            requires_llm_validation=classification.requires_llm_validation,
            requires_human_approval=classification.requires_human_approval,
            risk_score=estimated_risk,
            confidence_score=context.get('confidence', 0.7),
            aggressiveness_score=agg_score.global_score,
            recommendations=recommendations,
            warnings=warnings,
            blockers=blockers,
            narrative_explanation=narrative_explanation,
            decision_id=decision_id,
            evaluation_time_ms=elapsed_ms
        )
    
    def record_execution(
        self,
        decision_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Registrar resultado de ejecución de una decisión
        
        Args:
            decision_id: ID de la decisión (del ledger)
            success: Si la ejecución fue exitosa
            result: Resultado de la ejecución (opcional)
        """
        if success:
            self.ledger.mark_executed(decision_id)
        else:
            reason = result.get('error', 'unknown error') if result else 'execution failed'
            self.ledger.mark_failed(decision_id, reason)
    
    def reverse_decision(
        self,
        decision_id: str,
        reason: str
    ) -> bool:
        """
        Revertir una decisión ya ejecutada
        
        Args:
            decision_id: ID de la decisión
            reason: Razón de la reversión
        
        Returns:
            bool: True si se pudo revertir
        """
        return self.ledger.mark_reversed(decision_id, reason)
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen diario para humanos
        
        Returns:
            Resumen narrativo + métricas
        """
        # Get recent decisions (24h)
        end = datetime.now()
        start = end - timedelta(hours=24)
        recent_decisions = self.ledger.get_decisions_by_timerange(start, end)
        
        # Get aggressiveness status
        agg_status = self.agg_monitor.get_current_status()
        
        # Generate narrative report
        report = self.narrative.generate_daily_summary(
            decisions=recent_decisions,
            aggressiveness_data=agg_status
        )
        
        return {
            'report': report.to_markdown(),
            'metrics': report.key_metrics,
            'recommendations': report.recommendations,
            'alerts': report.alerts
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtener status actual del sistema
        
        Returns:
            Status completo con narrativa
        """
        # Get current aggressiveness
        agg_score = self.agg_monitor.evaluate_aggressiveness()
        
        # Get recent decisions (1h)
        end = datetime.now()
        start = end - timedelta(hours=1)
        recent_decisions = self.ledger.get_decisions_by_timerange(start, end)
        
        # Generate status report
        metrics = {
            'health': 'good' if agg_score.level == AggressivenessLevel.SAFE else 'warning',
            'decisions_1h': len(recent_decisions),
            'approval_rate': self.approvals / max(self.total_evaluations, 1),
            'in_cooldown': self.agg_monitor.is_in_cooldown()
        }
        
        report = self.narrative.generate_system_status(
            agg_score,
            recent_decisions,
            metrics
        )
        
        return {
            'status': report.to_markdown(),
            'aggressiveness': agg_score.get_summary(),
            'metrics': metrics,
            'recommendations': report.recommendations,
            'warnings': report.warnings
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            'bridge': {
                'total_evaluations': self.total_evaluations,
                'approvals': self.approvals,
                'rejections': self.rejections,
                'human_escalations': self.human_escalations,
                'approval_rate': self.approvals / max(self.total_evaluations, 1),
                'rejection_rate': self.rejections / max(self.total_evaluations, 1)
            },
            'classifier': self.classifier.get_statistics(),
            'risk_engine': self.risk_engine.get_statistics(),
            'aggressiveness_monitor': self.agg_monitor.get_statistics(),
            'ledger': self.ledger.get_statistics()
        }
    
    # Helper methods
    
    def _map_decision_to_action(self, decision_type: str) -> ActionType:
        """Map decision type string to ActionType enum"""
        mapping = {
            'content_boost': ActionType.BOOST_CONTENT,
            'content_post': ActionType.POST_CONTENT,
            'content_schedule': ActionType.SCHEDULE_CONTENT,
            'account_activation': ActionType.ACTIVATE_ACCOUNT,
            'account_scale': ActionType.SCALE_ACCOUNTS,
            'warmup_action': ActionType.WARMUP_ACTION,
            'like_batch': ActionType.LIKE_BATCH,
            'comment_batch': ActionType.COMMENT_BATCH,
            'follow_batch': ActionType.FOLLOW_BATCH,
        }
        return mapping.get(decision_type, ActionType.POST_CONTENT)
    
    def _map_to_decision_type(self, decision_type_str: str) -> DecisionType:
        """Map decision type string to DecisionType enum"""
        mapping = {
            'content_boost': DecisionType.CONTENT_BOOST,
            'content_suppress': DecisionType.CONTENT_SUPPRESS,
            'content_schedule': DecisionType.CONTENT_SCHEDULE,
            'account_activation': DecisionType.ACCOUNT_ACTIVATION,
            'account_pause': DecisionType.ACCOUNT_PAUSE,
            'account_warmup': DecisionType.ACCOUNT_WARMUP,
            'scale_up': DecisionType.SCALE_UP,
            'scale_down': DecisionType.SCALE_DOWN,
            'risk_mitigation': DecisionType.RISK_MITIGATION,
            'emergency_stop': DecisionType.EMERGENCY_STOP,
            'strategy_change': DecisionType.STRATEGY_CHANGE,
        }
        return mapping.get(decision_type_str, DecisionType.CONTENT_BOOST)
    
    def _generate_evaluation_narrative(
        self,
        decision_type: str,
        classification: Any,
        simulation: Optional[Any],
        agg_score: Any,
        approved: bool,
        blockers: List[str]
    ) -> str:
        """Generate narrative explanation of evaluation"""
        narrative = f"Decision '{decision_type}' was classified as {classification.level.value.upper()}. "
        
        if approved:
            narrative += "✓ APPROVED for execution. "
        else:
            narrative += "✗ REJECTED. "
        
        if blockers:
            narrative += f"Blockers: {', '.join(blockers)}. "
        
        if simulation:
            narrative += f"Risk simulation showed {simulation.total_risk_score:.0%} total risk. "
        
        narrative += f"System aggressiveness: {agg_score.level.value} ({agg_score.global_score:.2f})."
        
        return narrative
