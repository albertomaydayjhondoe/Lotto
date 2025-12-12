"""
SPRINT 10 - Global Supervisor Layer
Module 4: Gemini Validator - GEMINI 3.0 HARD VALIDATION LAYER

Capa de validación dura que evita decisiones dañinas, incoherentes,
peligrosas o potencialmente detectables.

Gemini valida SOLO reglas duras: operativas, cognitivas y de riesgo.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .supervisor_contract import (
    SummaryOutput,
    GPTAnalysis,
    ValidationResult,
    ValidationStatus,
    SupervisorConfig,
    SeverityLevel,
    RiskType,
)


class GeminiValidator:
    """
    Validador duro basado en Gemini 3.0.
    
    Responsibilities:
    - Validar reglas operativas (presupuesto, límites)
    - Validar reglas cognitivas (coherencia, no-alucinaciones)
    - Validar reglas de riesgo (identidad, patrones, detección)
    - Aprobar o rechazar decisiones
    - Generar ajustes requeridos
    
    NOT responsible for:
    - Proponer estrategia creativa
    - Generar contenido
    - Ejecutar acciones
    """
    
    def __init__(self, config: Optional[SupervisorConfig] = None):
        self.config = config or SupervisorConfig()
        
        # Modelo de Gemini
        self.model = self.config.gemini_model
        
        # API key (placeholder - en producción usar secrets)
        self.api_key = None  # TODO: Load from secrets
        
        # Modo de operación
        self.simulation_mode = True  # True para tests, False para producción
        
        # Thresholds
        self.risk_threshold_low = self.config.risk_threshold_low
        self.risk_threshold_medium = self.config.risk_threshold_medium
        self.risk_threshold_high = self.config.risk_threshold_high
        
        # Limits
        self.daily_budget_limit = self.config.daily_budget_limit
        self.monthly_budget_limit = self.config.monthly_budget_limit
        
        # Pattern detection thresholds
        self.pattern_similarity_threshold = self.config.pattern_similarity_threshold
        self.timing_similarity_threshold = self.config.timing_similarity_threshold
        self.identity_correlation_threshold = self.config.identity_correlation_threshold
    
    def validate(
        self,
        summary: SummaryOutput,
        gpt_analysis: GPTAnalysis
    ) -> ValidationResult:
        """
        Valida el resumen y análisis GPT con reglas duras.
        
        Args:
            summary: Resumen estructurado del sistema
            gpt_analysis: Análisis cognitivo de GPT
            
        Returns:
            ValidationResult con aprobación/rechazo y razones
        """
        validation_id = f"gemini_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()
        
        # En modo simulación, usar validación determinista
        if self.simulation_mode:
            return self._simulate_validation(validation_id, timestamp, summary, gpt_analysis)
        
        # En producción, usar API real de Gemini
        return self._real_gemini_validation(validation_id, timestamp, summary, gpt_analysis)
    
    def _simulate_validation(
        self,
        validation_id: str,
        timestamp: datetime,
        summary: SummaryOutput,
        gpt_analysis: GPTAnalysis
    ) -> ValidationResult:
        """
        Validación simulada con reglas deterministas.
        
        Aplica reglas duras de forma estricta.
        """
        violated_rules = []
        required_adjustments = []
        risk_breakdown = {}
        
        structured = summary.structured_data
        
        # ====================================================================
        # 1. REGLAS OPERATIVAS (Budget, Limits, Constraints)
        # ====================================================================
        
        operational_violations = self._validate_operational_rules(
            structured,
            violated_rules,
            required_adjustments,
            risk_breakdown
        )
        
        # ====================================================================
        # 2. REGLAS COGNITIVAS (Coherence, No-hallucinations)
        # ====================================================================
        
        cognitive_violations = self._validate_cognitive_rules(
            structured,
            gpt_analysis,
            violated_rules,
            required_adjustments,
            risk_breakdown
        )
        
        # ====================================================================
        # 3. REGLAS DE RIESGO (Identity, Patterns, Detection)
        # ====================================================================
        
        risk_violations = self._validate_risk_rules(
            structured,
            gpt_analysis,
            violated_rules,
            required_adjustments,
            risk_breakdown
        )
        
        # ====================================================================
        # 4. CALCULAR RISK SCORE GLOBAL
        # ====================================================================
        
        total_risk_score = self._calculate_global_risk_score(risk_breakdown)
        
        # ====================================================================
        # 5. DETERMINAR APROBACIÓN/RECHAZO
        # ====================================================================
        
        approved, status, reason = self._determine_approval(
            violated_rules,
            total_risk_score,
            summary.requires_attention,
            summary.critical_issues
        )
        
        # ====================================================================
        # 6. REGLAS DE VALIDACIÓN APLICADAS
        # ====================================================================
        
        validation_rules_applied = [
            "operational_budget_rules",
            "operational_action_limits",
            "cognitive_coherence_rules",
            "cognitive_hallucination_detection",
            "risk_identity_correlation",
            "risk_pattern_repetition",
            "risk_shadowban_signals",
            "risk_global_aggressiveness",
        ]
        
        return ValidationResult(
            validation_id=validation_id,
            timestamp=timestamp,
            approved=approved,
            status=status,
            reason=reason,
            risk_score=total_risk_score,
            risk_breakdown=risk_breakdown,
            required_adjustments=required_adjustments,
            violated_rules=violated_rules,
            model_used=self.model,
            validation_rules_applied=validation_rules_applied,
        )
    
    def _validate_operational_rules(
        self,
        structured: Dict[str, Any],
        violated_rules: List[str],
        required_adjustments: List[str],
        risk_breakdown: Dict[str, float]
    ) -> int:
        """Valida reglas operativas (presupuesto, límites, etc.)"""
        
        violations = 0
        
        costs = structured.get("costs", {})
        
        # Rule 1: Daily budget limit
        today_costs = costs.get("today", 0.0)
        if today_costs >= self.daily_budget_limit:
            violated_rules.append(
                f"DAILY_BUDGET_EXCEEDED: ${today_costs:.2f} >= ${self.daily_budget_limit:.2f}"
            )
            required_adjustments.append("HALT_ALL_SPENDING")
            required_adjustments.append("ALERT_HUMAN_IMMEDIATE")
            risk_breakdown["budget_exceeded"] = 1.0
            violations += 1
        elif today_costs >= self.daily_budget_limit * 0.9:
            # Warning zone
            risk_breakdown["budget_warning"] = 0.7
            required_adjustments.append("REDUCE_AD_SPEND")
        else:
            risk_breakdown["budget_ok"] = 0.1
        
        # Rule 2: Monthly budget limit
        month_costs = costs.get("month_accumulated", 0.0)
        budget_total = costs.get("budget_total", self.monthly_budget_limit)
        
        if month_costs >= budget_total:
            violated_rules.append(
                f"MONTHLY_BUDGET_EXCEEDED: ${month_costs:.2f} >= ${budget_total:.2f}"
            )
            required_adjustments.append("PAUSE_ALL_CAMPAIGNS")
            required_adjustments.append("ALERT_HUMAN_IMMEDIATE")
            risk_breakdown["monthly_budget_exceeded"] = 1.0
            violations += 1
        elif month_costs >= budget_total * 0.95:
            # Critical warning
            risk_breakdown["monthly_budget_critical"] = 0.85
            required_adjustments.append("REDUCE_SPENDING_IMMEDIATELY")
        
        # Rule 3: No se usa cuenta oficial incorrectamente
        # (Placeholder - depende de implementación específica)
        # Por ahora asumimos que no hay violaciones
        risk_breakdown["official_account_safety"] = 0.0
        
        # Rule 4: Tasa de acciones fallidas
        actions = structured.get("actions", [])
        if actions:
            failed_count = sum(1 for a in actions if not a.get("success", True))
            failure_rate = failed_count / len(actions)
            
            if failure_rate > 0.5:  # >50% failure
                violated_rules.append(
                    f"HIGH_FAILURE_RATE: {failure_rate:.1%} of actions failed"
                )
                required_adjustments.append("INVESTIGATE_API_ISSUES")
                required_adjustments.append("PAUSE_AUTOMATED_ACTIONS")
                risk_breakdown["action_failure_rate"] = min(1.0, failure_rate * 1.5)
                violations += 1
            elif failure_rate > 0.3:  # >30% failure
                risk_breakdown["action_failure_warning"] = failure_rate
        
        return violations
    
    def _validate_cognitive_rules(
        self,
        structured: Dict[str, Any],
        gpt_analysis: GPTAnalysis,
        violated_rules: List[str],
        required_adjustments: List[str],
        risk_breakdown: Dict[str, float]
    ) -> int:
        """Valida reglas cognitivas (coherencia, anti-alucinaciones)"""
        
        violations = 0
        
        # Rule 1: Decisiones coherentes con datos reales
        decisions = structured.get("decisions", [])
        metrics = structured.get("metrics", {})
        
        # Detectar contradicciones
        # Ejemplo: si engagement es bajo pero se decide "scale_ads", es incoherente
        if decisions and metrics:
            engagement = metrics.get("engagement", {})
            retention = engagement.get("avg_retention", 0)
            
            scale_decisions = [
                d for d in decisions 
                if d.get("type") in ["scale_ads", "increase_budget"]
            ]
            
            if scale_decisions and retention < 0.3:
                violated_rules.append(
                    "COGNITIVE_INCOHERENCE: Scaling ads with low engagement (retention < 30%)"
                )
                required_adjustments.append("REVIEW_DECISION_LOGIC")
                required_adjustments.append("IMPROVE_ENGAGEMENT_FIRST")
                risk_breakdown["cognitive_incoherence"] = 0.8
                violations += 1
        
        # Rule 2: GPT confidence razonable
        if gpt_analysis.confidence < 0.3:
            violated_rules.append(
                f"GPT_LOW_CONFIDENCE: Analysis confidence {gpt_analysis.confidence:.2f} too low"
            )
            required_adjustments.append("REQUIRE_HUMAN_REVIEW")
            risk_breakdown["gpt_confidence_low"] = 1.0 - gpt_analysis.confidence
            violations += 1
        elif gpt_analysis.confidence > 0.95:
            # Sospechosamente alta - posible alucinación
            violated_rules.append(
                f"GPT_OVERCONFIDENCE: Analysis confidence {gpt_analysis.confidence:.2f} suspiciously high"
            )
            required_adjustments.append("VALIDATE_WITH_HUMAN")
            risk_breakdown["gpt_overconfidence"] = 0.6
            violations += 1
        
        # Rule 3: No alucinaciones detectadas
        # Detectamos alucinaciones si GPT sugiere acciones sin datos
        if not decisions and not metrics and gpt_analysis.strategic_suggestions:
            # GPT está sugiriendo cosas sin tener datos - posible alucinación
            violated_rules.append(
                "GPT_HALLUCINATION_SUSPECTED: Suggestions without sufficient data"
            )
            required_adjustments.append("IGNORE_GPT_SUGGESTIONS")
            required_adjustments.append("COLLECT_MORE_DATA")
            risk_breakdown["hallucination_suspected"] = 0.75
            violations += 1
        
        return violations
    
    def _validate_risk_rules(
        self,
        structured: Dict[str, Any],
        gpt_analysis: GPTAnalysis,
        violated_rules: List[str],
        required_adjustments: List[str],
        risk_breakdown: Dict[str, float]
    ) -> int:
        """Valida reglas de riesgo (identidad, patrones, detección)"""
        
        violations = 0
        
        # Rule 1: Identity correlation risk
        metrics = structured.get("metrics", {})
        if metrics:
            risk_signals = metrics.get("risk_signals", {})
            correlation_signals = risk_signals.get("correlation_signals", 0)
            
            # Calcular score de correlación (normalizado)
            correlation_score = min(1.0, correlation_signals / 10.0)
            risk_breakdown["identity_correlation"] = correlation_score
            
            if correlation_score >= self.identity_correlation_threshold:
                violated_rules.append(
                    f"IDENTITY_CORRELATION_HIGH: {correlation_signals} signals detected"
                )
                required_adjustments.append("ROTATE_VPN_SERVERS")
                required_adjustments.append("CHANGE_PROXY_POOL")
                required_adjustments.append("REGENERATE_FINGERPRINTS")
                violations += 1
        
        # Rule 2: Pattern repetition risk
        detected_patterns = gpt_analysis.detected_patterns
        
        # Contar patrones repetitivos
        repetitive_patterns = [
            p for p in detected_patterns
            if "repetitive" in p.lower() or "pattern" in p.lower()
        ]
        
        if repetitive_patterns:
            pattern_score = min(1.0, len(repetitive_patterns) / 3.0)
            risk_breakdown["pattern_repetition"] = pattern_score
            
            if pattern_score >= self.pattern_similarity_threshold:
                violated_rules.append(
                    f"PATTERN_REPETITION_HIGH: {len(repetitive_patterns)} repetitive patterns"
                )
                required_adjustments.append("INCREASE_RANDOMNESS")
                required_adjustments.append("DIVERSIFY_BEHAVIOR")
                violations += 1
        else:
            risk_breakdown["pattern_ok"] = 0.1
        
        # Rule 3: Shadowban signals
        if metrics:
            risk_signals = metrics.get("risk_signals", {})
            shadowban_count = risk_signals.get("shadowban_signals", 0)
            
            shadowban_score = min(1.0, shadowban_count / 5.0)
            risk_breakdown["shadowban_signals"] = shadowban_score
            
            if shadowban_count > 0:
                violated_rules.append(
                    f"SHADOWBAN_SIGNALS_DETECTED: {shadowban_count} signals"
                )
                required_adjustments.append("PAUSE_AFFECTED_ACCOUNTS")
                required_adjustments.append("REDUCE_POSTING_FREQUENCY")
                required_adjustments.append("INCREASE_WARMUP_PERIOD")
                violations += 1
        
        # Rule 4: Global aggressiveness
        # Calculamos "agresividad" basada en:
        # - Número de acciones
        # - Frecuencia de publicaciones
        # - Gasto diario vs límite
        
        actions = structured.get("actions", [])
        costs = structured.get("costs", {})
        
        action_count = len(actions)
        daily_spend = costs.get("today", 0.0)
        
        # Score de agresividad (0-1)
        aggressiveness_score = 0.0
        
        # Por acciones (>20 acciones/día es agresivo)
        if action_count > 20:
            aggressiveness_score += min(0.5, action_count / 40.0)
        
        # Por gasto (>80% del límite diario es agresivo)
        if daily_spend > self.daily_budget_limit * 0.8:
            aggressiveness_score += 0.3
        
        # Por risks detectados
        if gpt_analysis.risk_signals:
            aggressiveness_score += min(0.2, len(gpt_analysis.risk_signals) / 10.0)
        
        risk_breakdown["global_aggressiveness"] = min(1.0, aggressiveness_score)
        
        if aggressiveness_score >= 0.8:
            violated_rules.append(
                f"AGGRESSIVENESS_TOO_HIGH: Score {aggressiveness_score:.2f}"
            )
            required_adjustments.append("REDUCE_ACTIVITY_GLOBALLY")
            required_adjustments.append("INCREASE_DELAYS")
            required_adjustments.append("PAUSE_NON_CRITICAL_ACTIONS")
            violations += 1
        
        return violations
    
    def _calculate_global_risk_score(self, risk_breakdown: Dict[str, float]) -> float:
        """
        Calcula el risk score global ponderado.
        
        Algunos riesgos son más críticos que otros.
        """
        weights = {
            # Críticos (peso alto)
            "budget_exceeded": 1.0,
            "monthly_budget_exceeded": 1.0,
            "shadowban_signals": 0.9,
            "identity_correlation": 0.85,
            
            # Altos (peso medio-alto)
            "action_failure_rate": 0.75,
            "pattern_repetition": 0.7,
            "cognitive_incoherence": 0.7,
            "global_aggressiveness": 0.7,
            
            # Medios (peso medio)
            "gpt_confidence_low": 0.5,
            "gpt_overconfidence": 0.5,
            "hallucination_suspected": 0.6,
            "budget_warning": 0.4,
            "monthly_budget_critical": 0.8,
            
            # Bajos (peso bajo)
            "action_failure_warning": 0.3,
            
            # OK signals (muy bajo)
            "budget_ok": 0.0,
            "pattern_ok": 0.0,
            "official_account_safety": 0.0,
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for risk_type, score in risk_breakdown.items():
            weight = weights.get(risk_type, 0.5)  # Default medium weight
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        global_score = weighted_sum / total_weight
        return min(1.0, global_score)
    
    def _determine_approval(
        self,
        violated_rules: List[str],
        risk_score: float,
        requires_attention: bool,
        critical_issues: List[str]
    ) -> Tuple[bool, ValidationStatus, str]:
        """
        Determina si se aprueba o rechaza la operación.
        
        Returns:
            (approved, status, reason)
        """
        
        # Rechazo inmediato si hay reglas críticas violadas
        critical_rule_keywords = [
            "BUDGET_EXCEEDED",
            "MONTHLY_BUDGET_EXCEEDED",
            "SHADOWBAN_SIGNALS_DETECTED",
            "HIGH_FAILURE_RATE",
        ]
        
        critical_violations = [
            rule for rule in violated_rules
            if any(kw in rule for kw in critical_rule_keywords)
        ]
        
        if critical_violations:
            return (
                False,
                ValidationStatus.REJECTED,
                f"Critical violations: {', '.join(critical_violations[:2])}"
            )
        
        # Rechazo si risk score muy alto
        if risk_score >= self.risk_threshold_high:
            return (
                False,
                ValidationStatus.REJECTED,
                f"Risk score too high: {risk_score:.2f} >= {self.risk_threshold_high}"
            )
        
        # Require human review si hay issues críticos
        if critical_issues and self.config.require_human_for_critical:
            return (
                False,
                ValidationStatus.NEEDS_HUMAN_REVIEW,
                f"Critical issues detected: {', '.join(critical_issues[:2])}"
            )
        
        # Require adjustments si hay violaciones no-críticas
        if violated_rules:
            return (
                False,
                ValidationStatus.REQUIRES_ADJUSTMENT,
                f"Violations detected: {', '.join(violated_rules[:2])}"
            )
        
        # Require adjustments si risk score medio-alto
        if risk_score >= self.risk_threshold_medium:
            return (
                False,
                ValidationStatus.REQUIRES_ADJUSTMENT,
                f"Risk score elevated: {risk_score:.2f}, adjustments recommended"
            )
        
        # Approved con observaciones si risk score bajo-medio
        if risk_score >= self.risk_threshold_low:
            return (
                True,
                ValidationStatus.APPROVED,
                f"Approved with caution: risk score {risk_score:.2f}"
            )
        
        # Approved completamente
        return (
            True,
            ValidationStatus.APPROVED,
            f"All constraints satisfied: risk score {risk_score:.2f}"
        )
    
    def _real_gemini_validation(
        self,
        validation_id: str,
        timestamp: datetime,
        summary: SummaryOutput,
        gpt_analysis: GPTAnalysis
    ) -> ValidationResult:
        """
        Validación real usando Gemini 3.0 API.
        
        TODO: Implementar cuando se tenga API key y budget.
        Por ahora, lanza excepción.
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Set api_key or enable simulation_mode."
            )
        
        # TODO: Implementar llamada real a Gemini API
        # Similar a GPT pero con enfoque en validación dura
        
        raise NotImplementedError(
            "Real Gemini API integration not yet implemented. "
            "Use simulation_mode=True for testing."
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_gemini_validator(config: Optional[SupervisorConfig] = None) -> GeminiValidator:
    """Helper para crear un GeminiValidator"""
    return GeminiValidator(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "GeminiValidator",
    "create_gemini_validator",
]
