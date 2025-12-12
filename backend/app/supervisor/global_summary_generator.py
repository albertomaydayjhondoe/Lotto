"""
SPRINT 10 - Global Supervisor Layer
Module 2: Global Summary Generator - E2B SUMMARY LAYER

Crea resúmenes estructurados y estandarizados de TODAS las decisiones,
acciones y estados importantes del sistema.

Este resumen es la "fuente de verdad" para GPT y Gemini.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .supervisor_contract import (
    SupervisionInput,
    SummaryOutput,
    Decision,
    Action,
    Metrics,
    CostReport,
    Risk,
    Anomaly,
    SeverityLevel,
    EngineSource,
    DecisionType,
    RiskType,
)


class GlobalSummaryGenerator:
    """
    Generador global de resúmenes estructurados.
    
    Responsibilities:
    - Recoger todas las señales del sistema
    - Estructurar en formato JSON estándar
    - Generar resumen en lenguaje natural
    - Identificar issues críticos
    - Detectar anomalías
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuración
        self.include_metadata = self.config.get("include_metadata", True)
        self.natural_language_detail_level = self.config.get("detail_level", "detailed")  # brief, detailed, verbose
        
        # Cache temporal para detección de anomalías
        self.recent_summaries: List[Dict[str, Any]] = []
        self.max_cache_size = 100
    
    def generate_summary(self, supervision_input: SupervisionInput) -> SummaryOutput:
        """
        Genera resumen completo del estado del sistema.
        
        Args:
            supervision_input: Input con todas las señales del sistema
            
        Returns:
            SummaryOutput con JSON estructurado y texto natural
        """
        summary_id = f"summary_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()
        
        # 1. Crear JSON estructurado
        structured_data = self._create_structured_json(supervision_input)
        
        # 2. Generar texto natural
        natural_language_summary = self._generate_natural_language(
            supervision_input,
            structured_data
        )
        
        # 3. Calcular estadísticas
        stats = self._calculate_statistics(supervision_input)
        
        # 4. Identificar issues críticos
        critical_issues = self._identify_critical_issues(supervision_input)
        
        # 5. Crear output
        summary_output = SummaryOutput(
            summary_id=summary_id,
            timestamp=timestamp,
            structured_data=structured_data,
            natural_language_summary=natural_language_summary,
            total_decisions=stats["total_decisions"],
            total_actions=stats["total_actions"],
            total_risks=stats["total_risks"],
            total_anomalies=stats["total_anomalies"],
            requires_attention=len(critical_issues) > 0,
            critical_issues=critical_issues,
        )
        
        # 6. Cachear para análisis histórico
        self._cache_summary(structured_data)
        
        return summary_output
    
    def _create_structured_json(self, input_data: SupervisionInput) -> Dict[str, Any]:
        """Crea el JSON estructurado estándar"""
        
        structured = {
            "timestamp": input_data.timestamp.isoformat(),
            "supervision_id": input_data.supervision_id,
            "engine_source": input_data.engine_source.value,
            "severity": input_data.severity.value,
            
            # Decisiones
            "decisions": [
                {
                    "type": d.type.value,
                    "description": d.description,
                    "engine_source": d.engine_source.value,
                    "timestamp": d.timestamp.isoformat(),
                    "reasoning": d.reasoning,
                    "alternatives_considered": d.alternatives_considered,
                    "confidence": d.confidence,
                    "metadata": d.metadata,
                }
                for d in input_data.decisions
            ],
            
            # Acciones
            "actions": [
                {
                    "action_id": a.action_id,
                    "type": a.type,
                    "engine_source": a.engine_source.value,
                    "timestamp": a.timestamp.isoformat(),
                    "target": a.target,
                    "parameters": a.parameters,
                    "result": a.result,
                    "success": a.success,
                    "error_message": a.error_message,
                }
                for a in input_data.actions
            ],
            
            # Métricas
            "metrics": self._serialize_metrics(input_data.metrics) if input_data.metrics else {},
            
            # Costes
            "costs": self._serialize_costs(input_data.costs) if input_data.costs else {},
            
            # Riesgos
            "risks": [
                {
                    "type": r.type.value,
                    "severity": r.severity.value,
                    "description": r.description,
                    "score": r.score,
                    "detected_at": r.detected_at.isoformat(),
                    "affected_targets": r.affected_targets,
                    "recommended_actions": r.recommended_actions,
                    "metadata": r.metadata,
                }
                for r in input_data.risks
            ],
            
            # Anomalías
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "type": a.type,
                    "description": a.description,
                    "severity": a.severity.value,
                    "detected_at": a.detected_at.isoformat(),
                    "value_expected": a.value_expected,
                    "value_actual": a.value_actual,
                    "affected_component": a.affected_component,
                    "requires_investigation": a.requires_investigation,
                }
                for a in input_data.anomalies
            ],
            
            # Contexto
            "context_summary": input_data.context_summary,
            
            # Metadata adicional
            "metadata": input_data.metadata if self.include_metadata else {},
        }
        
        return structured
    
    def _serialize_metrics(self, metrics: Metrics) -> Dict[str, Any]:
        """Serializa métricas a diccionario"""
        return {
            "engagement": {
                "avg_retention": metrics.avg_retention,
                "engagement_velocity": metrics.engagement_velocity,
                "avg_ctr": metrics.avg_ctr,
            },
            "ads": {
                "avg_cpm": metrics.avg_cpm,
                "avg_cpc": metrics.avg_cpc,
                "total_impressions": metrics.total_impressions,
                "total_clicks": metrics.total_clicks,
            },
            "risk_signals": {
                "shadowban_signals": metrics.shadowban_signals,
                "correlation_signals": metrics.correlation_signals,
            },
            "ml": {
                "confidence": metrics.ml_confidence,
            },
            "measured_at": metrics.measured_at.isoformat(),
            "additional": metrics.additional,
        }
    
    def _serialize_costs(self, costs: CostReport) -> Dict[str, Any]:
        """Serializa costes a diccionario"""
        return {
            "today": costs.today,
            "week_accumulated": costs.week_accumulated,
            "month_accumulated": costs.month_accumulated,
            "budget_remaining": costs.budget_remaining,
            "budget_total": costs.budget_total,
            "breakdown": {
                "satellite": costs.satellite_costs,
                "meta_ads": costs.meta_ads_costs,
                "telegram": costs.telegram_costs,
                "other": costs.other_costs,
            },
            "timestamp": costs.timestamp.isoformat(),
        }
    
    def _generate_natural_language(
        self,
        input_data: SupervisionInput,
        structured_data: Dict[str, Any]
    ) -> str:
        """Genera resumen en lenguaje natural"""
        
        lines = []
        
        # Header
        lines.append(f"=== SUPERVISION SUMMARY ===")
        lines.append(f"ID: {input_data.supervision_id}")
        lines.append(f"Time: {input_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Source: {input_data.engine_source.value}")
        lines.append(f"Severity: {input_data.severity.value.upper()}")
        lines.append("")
        
        # Decisiones
        if input_data.decisions:
            lines.append(f"DECISIONS ({len(input_data.decisions)}):")
            for i, decision in enumerate(input_data.decisions, 1):
                lines.append(f"  {i}. {decision.type.value}: {decision.description}")
                lines.append(f"     Reasoning: {decision.reasoning}")
                if decision.alternatives_considered:
                    lines.append(f"     Alternatives: {', '.join(decision.alternatives_considered)}")
                lines.append(f"     Confidence: {decision.confidence:.2f}")
            lines.append("")
        
        # Acciones
        if input_data.actions:
            lines.append(f"ACTIONS ({len(input_data.actions)}):")
            for i, action in enumerate(input_data.actions, 1):
                status = "✓" if action.success else "✗"
                lines.append(f"  {status} {i}. {action.type} on {action.target}")
                if action.result:
                    lines.append(f"     Result: {action.result}")
                if action.error_message:
                    lines.append(f"     Error: {action.error_message}")
            lines.append("")
        
        # Métricas
        if input_data.metrics:
            m = input_data.metrics
            lines.append("METRICS:")
            lines.append(f"  Engagement: retention={m.avg_retention:.2%}, velocity={m.engagement_velocity:.2f}, ctr={m.avg_ctr:.2%}")
            if m.total_impressions > 0:
                lines.append(f"  Ads: cpm=${m.avg_cpm:.2f}, cpc=${m.avg_cpc:.2f}, impressions={m.total_impressions}, clicks={m.total_clicks}")
            if m.shadowban_signals > 0 or m.correlation_signals > 0:
                lines.append(f"  Risk Signals: shadowban={m.shadowban_signals}, correlation={m.correlation_signals}")
            lines.append(f"  ML Confidence: {m.ml_confidence:.2%}")
            lines.append("")
        
        # Costes
        if input_data.costs:
            c = input_data.costs
            lines.append("COSTS:")
            lines.append(f"  Today: ${c.today:.2f}")
            lines.append(f"  Month: ${c.month_accumulated:.2f} / ${c.budget_total:.2f}")
            lines.append(f"  Remaining: ${c.budget_remaining:.2f}")
            budget_used_pct = (c.month_accumulated / c.budget_total * 100) if c.budget_total > 0 else 0
            lines.append(f"  Budget Used: {budget_used_pct:.1f}%")
            lines.append("")
        
        # Riesgos
        if input_data.risks:
            lines.append(f"RISKS ({len(input_data.risks)}):")
            for i, risk in enumerate(input_data.risks, 1):
                severity_icon = "🔴" if risk.severity == SeverityLevel.CRITICAL else "🟠" if risk.severity == SeverityLevel.HIGH else "🟡"
                lines.append(f"  {severity_icon} {i}. {risk.type.value} (score: {risk.score:.2f})")
                lines.append(f"     {risk.description}")
                if risk.affected_targets:
                    lines.append(f"     Affected: {', '.join(risk.affected_targets[:3])}{'...' if len(risk.affected_targets) > 3 else ''}")
            lines.append("")
        
        # Anomalías
        if input_data.anomalies:
            lines.append(f"ANOMALIES ({len(input_data.anomalies)}):")
            for i, anomaly in enumerate(input_data.anomalies, 1):
                lines.append(f"  {i}. {anomaly.type}: {anomaly.description}")
                if anomaly.value_expected is not None and anomaly.value_actual is not None:
                    lines.append(f"     Expected: {anomaly.value_expected}, Actual: {anomaly.value_actual}")
                if anomaly.requires_investigation:
                    lines.append(f"     ⚠️ Requires Investigation")
            lines.append("")
        
        # Context
        if input_data.context_summary:
            lines.append("CONTEXT:")
            lines.append(f"  {input_data.context_summary}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_statistics(self, input_data: SupervisionInput) -> Dict[str, int]:
        """Calcula estadísticas básicas"""
        return {
            "total_decisions": len(input_data.decisions),
            "total_actions": len(input_data.actions),
            "total_risks": len(input_data.risks),
            "total_anomalies": len(input_data.anomalies),
        }
    
    def _identify_critical_issues(self, input_data: SupervisionInput) -> List[str]:
        """Identifica issues críticos que requieren atención"""
        critical_issues = []
        
        # 1. Presupuesto excedido
        if input_data.costs:
            if input_data.costs.month_accumulated >= input_data.costs.budget_total:
                critical_issues.append("BUDGET_EXCEEDED: Monthly budget limit reached")
            elif input_data.costs.budget_remaining < (input_data.costs.budget_total * 0.1):
                critical_issues.append("BUDGET_LOW: Less than 10% budget remaining")
        
        # 2. Riesgos críticos
        critical_risks = [r for r in input_data.risks if r.severity == SeverityLevel.CRITICAL]
        if critical_risks:
            critical_issues.append(f"CRITICAL_RISKS: {len(critical_risks)} critical risks detected")
        
        # 3. Anomalías que requieren investigación
        investigation_anomalies = [a for a in input_data.anomalies if a.requires_investigation]
        if investigation_anomalies:
            critical_issues.append(f"ANOMALIES_INVESTIGATION: {len(investigation_anomalies)} anomalies require investigation")
        
        # 4. Acciones fallidas
        failed_actions = [a for a in input_data.actions if not a.success]
        if len(failed_actions) > 3:
            critical_issues.append(f"ACTION_FAILURES: {len(failed_actions)} failed actions")
        
        # 5. Señales de shadowban
        if input_data.metrics and input_data.metrics.shadowban_signals > 0:
            critical_issues.append(f"SHADOWBAN_SIGNALS: {input_data.metrics.shadowban_signals} signals detected")
        
        # 6. Correlación alta
        if input_data.metrics and input_data.metrics.correlation_signals > 5:
            critical_issues.append(f"CORRELATION_HIGH: {input_data.metrics.correlation_signals} correlation signals")
        
        return critical_issues
    
    def _cache_summary(self, structured_data: Dict[str, Any]):
        """Cachea el resumen para análisis histórico"""
        self.recent_summaries.append(structured_data)
        
        # Limitar tamaño del cache
        if len(self.recent_summaries) > self.max_cache_size:
            self.recent_summaries = self.recent_summaries[-self.max_cache_size:]
    
    def get_historical_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Genera resumen histórico de las últimas N horas.
        
        Útil para detectar patrones y tendencias.
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_summaries = [
            s for s in self.recent_summaries
            if datetime.fromisoformat(s["timestamp"]) >= cutoff_time
        ]
        
        if not recent_summaries:
            return {
                "period_hours": hours,
                "total_summaries": 0,
                "message": "No summaries in this period"
            }
        
        # Agregar estadísticas
        total_decisions = sum(len(s.get("decisions", [])) for s in recent_summaries)
        total_actions = sum(len(s.get("actions", [])) for s in recent_summaries)
        total_risks = sum(len(s.get("risks", [])) for s in recent_summaries)
        total_anomalies = sum(len(s.get("anomalies", [])) for s in recent_summaries)
        
        # Costes totales
        total_costs = sum(
            s.get("costs", {}).get("today", 0.0)
            for s in recent_summaries
        )
        
        return {
            "period_hours": hours,
            "total_summaries": len(recent_summaries),
            "aggregated_stats": {
                "total_decisions": total_decisions,
                "total_actions": total_actions,
                "total_risks": total_risks,
                "total_anomalies": total_anomalies,
                "total_costs": total_costs,
            },
            "summaries": recent_summaries,
        }
    
    def detect_pattern_repetition(
        self,
        lookback_hours: int = 6
    ) -> Dict[str, Any]:
        """
        Detecta repetición de patrones sospechosa.
        
        Returns:
            Dict con patrones detectados y score de repetición
        """
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        recent_summaries = [
            s for s in self.recent_summaries
            if datetime.fromisoformat(s["timestamp"]) >= cutoff_time
        ]
        
        if len(recent_summaries) < 3:
            return {
                "pattern_detected": False,
                "repetition_score": 0.0,
                "message": "Insufficient data for pattern detection"
            }
        
        # Extraer secuencias de tipos de decisiones
        decision_sequences = []
        for summary in recent_summaries:
            decisions = summary.get("decisions", [])
            if decisions:
                sequence = tuple(d.get("type") for d in decisions)
                decision_sequences.append(sequence)
        
        # Calcular repetición
        if not decision_sequences:
            return {
                "pattern_detected": False,
                "repetition_score": 0.0,
                "message": "No decision sequences found"
            }
        
        # Contar secuencias únicas
        unique_sequences = len(set(decision_sequences))
        total_sequences = len(decision_sequences)
        
        # Score de repetición (inverso de diversidad)
        repetition_score = 1.0 - (unique_sequences / total_sequences)
        
        return {
            "pattern_detected": repetition_score > 0.7,
            "repetition_score": repetition_score,
            "total_sequences": total_sequences,
            "unique_sequences": unique_sequences,
            "most_common_sequence": max(set(decision_sequences), key=decision_sequences.count) if decision_sequences else None,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_summary_generator(config: Optional[Dict[str, Any]] = None) -> GlobalSummaryGenerator:
    """Helper para crear un GlobalSummaryGenerator"""
    return GlobalSummaryGenerator(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "GlobalSummaryGenerator",
    "create_summary_generator",
]
