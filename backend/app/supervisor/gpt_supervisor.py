"""
SPRINT 10 - Global Supervisor Layer
Module 3: GPT Supervisor - GPT COGNITIVE ANALYZER

Capa de análisis cognitivo que detecta patrones, identifica riesgos,
propone ajustes y explica decisiones.

GPT NO ejecuta acciones, solo analiza y recomienda.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .supervisor_contract import (
    SummaryOutput,
    GPTAnalysis,
    SeverityLevel,
)


class GPTSupervisor:
    """
    Supervisor cognitivo basado en GPT.
    
    Responsibilities:
    - Analizar resúmenes del sistema
    - Detectar patrones y tendencias
    - Identificar señales de riesgo
    - Proponer ajustes estratégicos
    - Explicar decisiones
    
    NOT responsible for:
    - Ejecutar acciones
    - Publicar contenido
    - Escalar presupuestos
    - Tocar cuentas directamente
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuración GPT
        self.model = self.config.get("model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_tokens = self.config.get("max_tokens", 1500)
        
        # API key (placeholder - en producción usar secrets)
        self.api_key = self.config.get("api_key", None)
        
        # Modo de operación
        self.simulation_mode = self.config.get("simulation_mode", True)  # True para tests
        
        # Thresholds para detección
        self.pattern_threshold = self.config.get("pattern_threshold", 0.7)
        self.risk_threshold = self.config.get("risk_threshold", 0.6)
        
        # Context window para análisis histórico
        self.context_window_hours = self.config.get("context_window_hours", 6)
    
    def analyze(self, summary: SummaryOutput) -> GPTAnalysis:
        """
        Analiza el resumen del sistema y genera insights cognitivos.
        
        Args:
            summary: SummaryOutput del GlobalSummaryGenerator
            
        Returns:
            GPTAnalysis con observaciones, patrones, sugerencias, etc.
        """
        analysis_id = f"gpt_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()
        
        # En modo simulación, usar análisis determinista
        if self.simulation_mode:
            return self._simulate_analysis(analysis_id, timestamp, summary)
        
        # En producción, usar API real de GPT
        return self._real_gpt_analysis(analysis_id, timestamp, summary)
    
    def _simulate_analysis(
        self,
        analysis_id: str,
        timestamp: datetime,
        summary: SummaryOutput
    ) -> GPTAnalysis:
        """
        Análisis simulado para tests y desarrollo.
        
        Usa reglas deterministas para generar análisis coherente.
        """
        observations = []
        detected_patterns = []
        strategic_suggestions = []
        risk_signals = []
        recommended_adjustments = []
        
        structured = summary.structured_data
        
        # 1. OBSERVACIONES - Análisis descriptivo
        observations.append(
            f"System processed {summary.total_decisions} decisions and "
            f"{summary.total_actions} actions in this cycle"
        )
        
        if summary.total_risks > 0:
            observations.append(
                f"Detected {summary.total_risks} risk signals requiring attention"
            )
        
        if summary.total_anomalies > 0:
            observations.append(
                f"Identified {summary.total_anomalies} anomalies in system behavior"
            )
        
        # Análisis de métricas
        metrics = structured.get("metrics", {})
        if metrics:
            engagement = metrics.get("engagement", {})
            if engagement.get("avg_retention", 0) > 0.6:
                observations.append(
                    f"Strong engagement metrics: {engagement.get('avg_retention', 0):.1%} average retention"
                )
            elif engagement.get("avg_retention", 0) < 0.3:
                observations.append(
                    f"Low engagement detected: {engagement.get('avg_retention', 0):.1%} retention (below threshold)"
                )
        
        # Análisis de costes
        costs = structured.get("costs", {})
        if costs:
            budget_used_pct = (
                costs.get("month_accumulated", 0) / costs.get("budget_total", 1) * 100
                if costs.get("budget_total", 0) > 0 else 0
            )
            observations.append(
                f"Budget utilization: {budget_used_pct:.1f}% of monthly allocation"
            )
        
        # 2. PATRONES DETECTADOS
        decisions = structured.get("decisions", [])
        if decisions:
            decision_types = [d.get("type") for d in decisions]
            unique_types = set(decision_types)
            
            if len(decision_types) > 3 and len(unique_types) < 3:
                detected_patterns.append(
                    f"Repetitive decision pattern detected: {len(decision_types)} decisions, "
                    f"only {len(unique_types)} unique types"
                )
            
            # Análisis de confianza en decisiones
            confidences = [d.get("confidence", 0) for d in decisions if "confidence" in d]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence < 0.5:
                    detected_patterns.append(
                        f"Low decision confidence pattern: {avg_confidence:.2f} average"
                    )
        
        # Análisis de acciones
        actions = structured.get("actions", [])
        if actions:
            failed_actions = [a for a in actions if not a.get("success", True)]
            if len(failed_actions) > 2:
                detected_patterns.append(
                    f"High failure rate detected: {len(failed_actions)}/{len(actions)} actions failed"
                )
        
        # 3. SUGERENCIAS ESTRATÉGICAS
        
        # Basadas en engagement
        if metrics:
            engagement = metrics.get("engagement", {})
            retention = engagement.get("avg_retention", 0)
            velocity = engagement.get("engagement_velocity", 0)
            
            if retention < 0.4 and velocity < 0.5:
                strategic_suggestions.append(
                    "Consider content strategy adjustment: both retention and velocity below optimal"
                )
                strategic_suggestions.append(
                    "Recommend A/B testing different content styles or timing patterns"
                )
            
            # Análisis de ads
            ads = metrics.get("ads", {})
            if ads.get("avg_cpm", 0) > 15.0:
                strategic_suggestions.append(
                    f"High CPM detected (${ads.get('avg_cpm', 0):.2f}): consider audience refinement"
                )
        
        # Basadas en costes
        if costs:
            remaining_pct = (
                costs.get("budget_remaining", 0) / costs.get("budget_total", 1) * 100
                if costs.get("budget_total", 0) > 0 else 0
            )
            
            if remaining_pct < 20:
                strategic_suggestions.append(
                    f"Budget running low ({remaining_pct:.1f}% remaining): recommend spending pace review"
                )
            elif remaining_pct > 80 and costs.get("month_accumulated", 0) > 0:
                # Mucho presupuesto sin usar - quizá muy conservador
                day_of_month = datetime.now().day
                if day_of_month > 15:
                    strategic_suggestions.append(
                        f"Budget underutilization: {remaining_pct:.1f}% remaining mid-month, "
                        "consider scaling opportunities"
                    )
        
        # 4. SEÑALES DE RIESGO
        
        risks = structured.get("risks", [])
        for risk in risks:
            severity = risk.get("severity", "low")
            risk_type = risk.get("type", "unknown")
            score = risk.get("score", 0)
            
            if severity in ["high", "critical"]:
                risk_signals.append(
                    f"{severity.upper()}: {risk_type} (score: {score:.2f}) - {risk.get('description', 'No description')}"
                )
            elif score > self.risk_threshold:
                risk_signals.append(
                    f"Elevated risk: {risk_type} (score: {score:.2f})"
                )
        
        # Riesgos derivados de anomalías
        anomalies = structured.get("anomalies", [])
        investigation_required = [a for a in anomalies if a.get("requires_investigation", False)]
        if investigation_required:
            risk_signals.append(
                f"{len(investigation_required)} anomalies require immediate investigation"
            )
        
        # Shadowban signals
        risk_signals_data = metrics.get("risk_signals", {}) if metrics else {}
        shadowban_count = risk_signals_data.get("shadowban_signals", 0)
        if shadowban_count > 0:
            risk_signals.append(
                f"SHADOWBAN WARNING: {shadowban_count} signals detected - reduce posting aggressiveness"
            )
        
        # Correlation signals
        correlation_count = risk_signals_data.get("correlation_signals", 0)
        if correlation_count > 5:
            risk_signals.append(
                f"HIGH CORRELATION: {correlation_count} signals - accounts may be linked by platform"
            )
        
        # 5. AJUSTES RECOMENDADOS
        
        # Si hay muchos riesgos, recomendar modo conservador
        if len(risk_signals) > 3:
            recommended_adjustments.append("REDUCE_AGGRESSIVENESS")
            recommended_adjustments.append("INCREASE_RANDOMNESS")
            recommended_adjustments.append("REVIEW_IDENTITY_ISOLATION")
        
        # Si hay shadowban signals
        if shadowban_count > 0:
            recommended_adjustments.append("PAUSE_AFFECTED_ACCOUNTS")
            recommended_adjustments.append("INCREASE_POST_INTERVALS")
            recommended_adjustments.append("REDUCE_DAILY_POSTS")
        
        # Si hay alta correlación
        if correlation_count > 5:
            recommended_adjustments.append("ROTATE_VPN_SERVERS")
            recommended_adjustments.append("CHANGE_PROXY_POOL")
            recommended_adjustments.append("REGENERATE_FINGERPRINTS")
        
        # Si engagement bajo
        if metrics:
            engagement = metrics.get("engagement", {})
            if engagement.get("avg_retention", 0) < 0.3:
                recommended_adjustments.append("ADJUST_CONTENT_STRATEGY")
                recommended_adjustments.append("TEST_DIFFERENT_NICHES")
        
        # Si presupuesto muy bajo
        if costs and costs.get("budget_remaining", 0) < (costs.get("budget_total", 1) * 0.1):
            recommended_adjustments.append("REDUCE_AD_SPEND")
            recommended_adjustments.append("PAUSE_LOW_PERFORMING_CAMPAIGNS")
        
        # Si muchas acciones fallidas
        if actions:
            failed_actions = [a for a in actions if not a.get("success", True)]
            if len(failed_actions) > len(actions) * 0.3:  # >30% failure rate
                recommended_adjustments.append("INVESTIGATE_API_ISSUES")
                recommended_adjustments.append("CHECK_ACCOUNT_CREDENTIALS")
        
        # 6. CALCULAR CONFIANZA DEL ANÁLISIS
        
        # Confianza basada en cantidad de datos disponibles
        confidence = 0.5  # Base
        
        if summary.total_decisions > 0:
            confidence += 0.1
        if summary.total_actions > 0:
            confidence += 0.1
        if metrics:
            confidence += 0.1
        if costs:
            confidence += 0.1
        if len(observations) > 3:
            confidence += 0.1
        
        # Reducir confianza si hay muchas anomalías (datos poco fiables)
        if summary.total_anomalies > 5:
            confidence -= 0.1
        
        confidence = max(0.0, min(1.0, confidence))
        
        # 7. GENERAR REASONING
        reasoning = self._generate_reasoning(
            observations,
            detected_patterns,
            risk_signals,
            strategic_suggestions
        )
        
        return GPTAnalysis(
            analysis_id=analysis_id,
            timestamp=timestamp,
            observations=observations,
            detected_patterns=detected_patterns,
            strategic_suggestions=strategic_suggestions,
            risk_signals=risk_signals,
            recommended_adjustments=recommended_adjustments,
            confidence=confidence,
            model_used=self.model,
            reasoning=reasoning,
        )
    
    def _generate_reasoning(
        self,
        observations: List[str],
        patterns: List[str],
        risks: List[str],
        suggestions: List[str]
    ) -> str:
        """Genera explicación del razonamiento del análisis"""
        
        lines = []
        
        lines.append("COGNITIVE ANALYSIS REASONING:")
        lines.append("")
        
        if observations:
            lines.append("Key Observations:")
            for obs in observations[:3]:  # Top 3
                lines.append(f"  - {obs}")
            lines.append("")
        
        if patterns:
            lines.append("Pattern Detection:")
            for pattern in patterns:
                lines.append(f"  - {pattern}")
            lines.append("")
        
        if risks:
            lines.append("Risk Assessment:")
            for risk in risks[:3]:  # Top 3 risks
                lines.append(f"  - {risk}")
            lines.append("")
        
        if suggestions:
            lines.append("Strategic Direction:")
            for suggestion in suggestions[:2]:  # Top 2 suggestions
                lines.append(f"  - {suggestion}")
            lines.append("")
        
        lines.append("Analysis completed with deterministic cognitive rules.")
        
        return "\n".join(lines)
    
    def _real_gpt_analysis(
        self,
        analysis_id: str,
        timestamp: datetime,
        summary: SummaryOutput
    ) -> GPTAnalysis:
        """
        Análisis real usando OpenAI GPT API.
        
        TODO: Implementar cuando se tenga API key y budget para GPT-4.
        Por ahora, lanza excepción.
        """
        if not self.api_key:
            raise ValueError(
                "GPT API key not configured. "
                "Set api_key in config or enable simulation_mode."
            )
        
        # TODO: Implementar llamada real a OpenAI API
        # Pseudocódigo:
        # 
        # import openai
        # 
        # prompt = self._build_prompt(summary)
        # 
        # response = openai.ChatCompletion.create(
        #     model=self.model,
        #     messages=[
        #         {"role": "system", "content": SYSTEM_PROMPT},
        #         {"role": "user", "content": prompt}
        #     ],
        #     temperature=self.temperature,
        #     max_tokens=self.max_tokens
        # )
        # 
        # return self._parse_gpt_response(response, analysis_id, timestamp)
        
        raise NotImplementedError(
            "Real GPT API integration not yet implemented. "
            "Use simulation_mode=True for testing."
        )
    
    def _build_prompt(self, summary: SummaryOutput) -> str:
        """Construye el prompt para GPT (para uso futuro)"""
        
        prompt = f"""
You are a cognitive analyzer for the STAKAZO viral content automation system.

Your role is to:
- Analyze system behavior and metrics
- Detect patterns and anomalies
- Identify strategic opportunities and risks
- Recommend adjustments to improve performance
- Explain your reasoning clearly

You MUST NOT:
- Execute any actions
- Make definitive decisions
- Access or modify accounts
- Spend budget

SYSTEM SUMMARY:
{summary.natural_language_summary}

STRUCTURED DATA:
{json.dumps(summary.structured_data, indent=2)}

Please provide your analysis in the following JSON format:
{{
  "observations": [list of key observations],
  "detected_patterns": [list of patterns detected],
  "strategic_suggestions": [list of strategic recommendations],
  "risk_signals": [list of risk signals and warnings],
  "recommended_adjustments": [list of specific adjustments to make],
  "confidence": <float 0-1>,
  "reasoning": "<detailed explanation of your analysis>"
}}
"""
        return prompt


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_gpt_supervisor(config: Optional[Dict[str, Any]] = None) -> GPTSupervisor:
    """Helper para crear un GPTSupervisor"""
    return GPTSupervisor(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "GPTSupervisor",
    "create_gpt_supervisor",
]
