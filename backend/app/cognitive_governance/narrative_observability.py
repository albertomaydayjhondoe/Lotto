"""
SPRINT 14 - Narrative Observability (Observabilidad Narrativa Humana)

Objetivo:
Convertir todas las decisiones y estados del sistema en mensajes narrativos
comprensibles para un humano.

Outputs:
- Resumen diario
- Explicación de decisiones clave
- Alertas semánticas
- Análisis de riesgo

Ejemplo:
> "Hoy el sistema priorizó YouTube porque 3 vídeos estaban a 5 comentarios del breakout.
Se evitó escalar debido a un aumento del riesgo de repetición.
No se detectó correlación de identidad."

Se muestra automáticamente en:
- Dashboard (Sprint 13)
- Telegram (si habilitado)

Integración:
- Decision Ledger (fuente de datos)
- Risk Simulation (contexto de riesgo)
- Aggressiveness Monitor (estado del sistema)
- Orchestrator (decisiones tomadas)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum


class NarrativeType(Enum):
    """Tipos de narrativas"""
    DAILY_SUMMARY = "daily_summary"
    DECISION_EXPLANATION = "decision_explanation"
    RISK_ALERT = "risk_alert"
    SYSTEM_STATUS = "system_status"
    MILESTONE_ACHIEVED = "milestone_achieved"
    ERROR_REPORT = "error_report"


@dataclass
class DecisionExplanation:
    """Explicación narrativa de una decisión"""
    decision_id: str
    timestamp: datetime
    title: str  # ej: "Boosted YouTube video YT_014"
    explanation: str  # Párrafo explicativo completo
    reasoning_points: List[str]  # Puntos clave del razonamiento
    confidence: str  # "high", "medium", "low"
    risk_assessment: str  # Narrativa de riesgo
    outcome_expected: str  # Qué se espera que pase
    
    def to_markdown(self) -> str:
        """Convert to markdown for display"""
        md = f"## {self.title}\n\n"
        md += f"**Decision ID:** {self.decision_id}  \n"
        md += f"**Time:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  \n"
        md += f"**Confidence:** {self.confidence}  \n\n"
        md += f"{self.explanation}\n\n"
        md += "### Key Reasoning:\n"
        for point in self.reasoning_points:
            md += f"- {point}\n"
        md += f"\n### Risk Assessment:\n{self.risk_assessment}\n\n"
        md += f"### Expected Outcome:\n{self.outcome_expected}\n"
        return md


@dataclass
class NarrativeReport:
    """Reporte narrativo completo"""
    report_type: NarrativeType
    timestamp: datetime
    title: str
    summary: str  # Resumen ejecutivo
    body: str  # Narrativa completa
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Convert to markdown"""
        md = f"# {self.title}\n\n"
        md += f"**Type:** {self.report_type.value}  \n"
        md += f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  \n\n"
        md += f"## Summary\n{self.summary}\n\n"
        md += f"## Details\n{self.body}\n\n"
        
        if self.key_metrics:
            md += "## Key Metrics\n"
            for key, value in self.key_metrics.items():
                md += f"- **{key}:** {value}\n"
            md += "\n"
        
        if self.recommendations:
            md += "## Recommendations\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
            md += "\n"
        
        if self.alerts:
            md += "## ⚠️ Alerts\n"
            for alert in self.alerts:
                md += f"- {alert}\n"
            md += "\n"
        
        return md


class NarrativeObservability:
    """
    Generador de narrativas humanas sobre el sistema
    
    Características:
    - Lenguaje natural y claro
    - Contexto completo
    - Explicaciones causales
    - Recomendaciones accionables
    - Alertas proactivas
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.language = self.config.get('language', 'en')  # 'en' o 'es'
        
        # Cache de narrativas
        self._narrative_cache: List[NarrativeReport] = []
        self._cache_limit = 100
    
    def explain_decision(
        self,
        decision_record: Any,  # DecisionRecord from decision_ledger
        simulation_result: Optional[Any] = None  # SimulationResult from risk_simulation
    ) -> DecisionExplanation:
        """
        Generar explicación narrativa de una decisión
        
        Args:
            decision_record: DecisionRecord del ledger
            simulation_result: SimulationResult opcional para contexto de riesgo
        
        Returns:
            DecisionExplanation con narrativa completa
        """
        # Generar título
        title = self._generate_decision_title(decision_record)
        
        # Generar explicación completa
        explanation = self._generate_decision_explanation(decision_record)
        
        # Extraer puntos clave del reasoning
        reasoning_points = decision_record.reasoning[:5]  # Top 5
        
        # Determinar nivel de confianza narrativo
        if decision_record.confidence >= 0.8:
            confidence = "high"
        elif decision_record.confidence >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generar narrativa de riesgo
        risk_assessment = self._generate_risk_narrative(
            decision_record,
            simulation_result
        )
        
        # Generar narrativa de outcome esperado
        outcome_expected = self._generate_outcome_narrative(decision_record)
        
        return DecisionExplanation(
            decision_id=decision_record.decision_id,
            timestamp=decision_record.timestamp,
            title=title,
            explanation=explanation,
            reasoning_points=reasoning_points,
            confidence=confidence,
            risk_assessment=risk_assessment,
            outcome_expected=outcome_expected
        )
    
    def generate_daily_summary(
        self,
        decisions: List[Any],  # List[DecisionRecord]
        aggressiveness_data: Optional[Dict[str, Any]] = None,
        date: Optional[datetime] = None
    ) -> NarrativeReport:
        """
        Generar resumen diario del sistema
        
        Args:
            decisions: Lista de decisiones tomadas hoy
            aggressiveness_data: Datos de agresividad del día
            date: Fecha del resumen (default: hoy)
        
        Returns:
            NarrativeReport con resumen completo del día
        """
        date = date or datetime.now()
        
        # Análisis de decisiones
        total_decisions = len(decisions)
        critical_decisions = sum(1 for d in decisions if d.is_critical())
        avg_confidence = sum(d.confidence for d in decisions) / max(total_decisions, 1)
        avg_risk = sum(d.risk_score for d in decisions) / max(total_decisions, 1)
        
        # Decisiones por tipo
        by_type = {}
        for d in decisions:
            t = d.decision_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        # Generar narrativa
        summary = self._generate_daily_summary_text(
            total_decisions,
            critical_decisions,
            avg_confidence,
            avg_risk,
            by_type
        )
        
        body = self._generate_daily_body_text(decisions, aggressiveness_data)
        
        # Métricas clave
        key_metrics = {
            'Total Decisions': total_decisions,
            'Critical Decisions': critical_decisions,
            'Avg Confidence': f"{avg_confidence:.2f}",
            'Avg Risk Score': f"{avg_risk:.2f}",
            'Most Common Action': max(by_type.items(), key=lambda x: x[1])[0] if by_type else 'none'
        }
        
        # Recomendaciones
        recommendations = self._generate_daily_recommendations(
            avg_confidence,
            avg_risk,
            aggressiveness_data
        )
        
        # Alertas
        alerts = self._generate_daily_alerts(decisions, aggressiveness_data)
        
        return NarrativeReport(
            report_type=NarrativeType.DAILY_SUMMARY,
            timestamp=datetime.now(),
            title=f"Daily Summary - {date.strftime('%Y-%m-%d')}",
            summary=summary,
            body=body,
            key_metrics=key_metrics,
            recommendations=recommendations,
            alerts=alerts
        )
    
    def generate_risk_alert(
        self,
        risk_data: Dict[str, Any],
        severity: str = "medium"
    ) -> NarrativeReport:
        """
        Generar alerta de riesgo narrativa
        
        Args:
            risk_data: Datos del riesgo detectado
            severity: "low", "medium", "high", "critical"
        
        Returns:
            NarrativeReport con alerta
        """
        title = f"⚠️ Risk Alert ({severity.upper()})"
        
        summary = self._generate_risk_alert_summary(risk_data, severity)
        body = self._generate_risk_alert_body(risk_data)
        
        recommendations = risk_data.get('recommendations', [])
        alerts = [f"{severity.upper()} severity risk detected"]
        
        return NarrativeReport(
            report_type=NarrativeType.RISK_ALERT,
            timestamp=datetime.now(),
            title=title,
            summary=summary,
            body=body,
            recommendations=recommendations,
            alerts=alerts
        )
    
    def generate_system_status(
        self,
        aggressiveness_score: Any,  # AggressivenessScore
        recent_decisions: List[Any],  # List[DecisionRecord]
        metrics: Dict[str, Any]
    ) -> NarrativeReport:
        """
        Generar status narrativo del sistema
        
        Returns:
            NarrativeReport con estado actual
        """
        title = "System Status Report"
        
        summary = self._generate_system_status_summary(
            aggressiveness_score,
            len(recent_decisions),
            metrics
        )
        
        body = self._generate_system_status_body(
            aggressiveness_score,
            recent_decisions,
            metrics
        )
        
        key_metrics = {
            'Aggressiveness Level': aggressiveness_score.level.value if aggressiveness_score else 'unknown',
            'Recent Decisions (1h)': len(recent_decisions),
            'System Health': metrics.get('health', 'unknown')
        }
        
        recommendations = aggressiveness_score.recommendations if aggressiveness_score else []
        alerts = aggressiveness_score.warnings if aggressiveness_score else []
        
        return NarrativeReport(
            report_type=NarrativeType.SYSTEM_STATUS,
            timestamp=datetime.now(),
            title=title,
            summary=summary,
            body=body,
            key_metrics=key_metrics,
            recommendations=recommendations,
            alerts=alerts
        )
    
    # Helper methods for narrative generation
    
    def _generate_decision_title(self, decision: Any) -> str:
        """Generate short title for decision"""
        action = decision.decision_type.value.replace('_', ' ').title()
        target = decision.chosen[:20] if len(decision.chosen) > 20 else decision.chosen
        return f"{action}: {target}"
    
    def _generate_decision_explanation(self, decision: Any) -> str:
        """Generate full explanation paragraph"""
        actor = decision.actor
        action = decision.decision_type.value.replace('_', ' ')
        chosen = decision.chosen
        confidence = decision.confidence
        
        explanation = f"The {actor} decided to {action} on '{chosen}' "
        explanation += f"with {confidence:.0%} confidence. "
        
        if decision.reasoning:
            top_reason = decision.reasoning[0]
            explanation += f"Primary reasoning: {top_reason}. "
        
        if decision.alternatives_considered:
            alt_count = len(decision.alternatives_considered)
            explanation += f"{alt_count} alternative(s) were evaluated before this decision."
        
        return explanation
    
    def _generate_risk_narrative(self, decision: Any, simulation: Optional[Any]) -> str:
        """Generate risk assessment narrative"""
        risk_score = decision.risk_score
        
        if risk_score < 0.3:
            assessment = "Risk level is LOW. "
        elif risk_score < 0.5:
            assessment = "Risk level is MODERATE. "
        elif risk_score < 0.7:
            assessment = "Risk level is ELEVATED. "
        else:
            assessment = "Risk level is HIGH. "
        
        assessment += f"Overall risk score: {risk_score:.2f}. "
        
        if simulation:
            assessment += f"Simulation showed {simulation.shadowban_probability:.0%} shadowban probability "
            assessment += f"and {simulation.pattern_similarity:.0%} pattern similarity."
        
        return assessment
    
    def _generate_outcome_narrative(self, decision: Any) -> str:
        """Generate expected outcome narrative"""
        if decision.expected_impact:
            impacts = []
            for key, value in decision.expected_impact.items():
                sign = "+" if value > 0 else ""
                impacts.append(f"{key} {sign}{value:.1%}")
            return f"Expected impact: {', '.join(impacts)}."
        return "Expected outcome: System will proceed with this action and monitor results."
    
    def _generate_daily_summary_text(
        self,
        total: int,
        critical: int,
        avg_conf: float,
        avg_risk: float,
        by_type: Dict[str, int]
    ) -> str:
        """Generate daily summary text"""
        summary = f"Today the system made {total} decision(s), including {critical} critical decision(s). "
        summary += f"Average confidence was {avg_conf:.0%} with average risk score of {avg_risk:.2f}. "
        
        if by_type:
            most_common = max(by_type.items(), key=lambda x: x[1])
            summary += f"Most common action: {most_common[0]} ({most_common[1]} times)."
        
        return summary
    
    def _generate_daily_body_text(
        self,
        decisions: List[Any],
        agg_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate detailed daily body text"""
        body = "## Decision Breakdown\n\n"
        
        # Top 3 most important decisions
        critical_decisions = [d for d in decisions if d.is_critical()]
        if critical_decisions:
            body += "### Critical Decisions:\n"
            for d in critical_decisions[:3]:
                body += f"- {d.decision_type.value}: {d.chosen} (confidence: {d.confidence:.0%})\n"
            body += "\n"
        
        # Aggressiveness analysis
        if agg_data:
            body += "### System Aggressiveness:\n"
            level = agg_data.get('level', 'unknown')
            score = agg_data.get('global_score', 0)
            body += f"- Level: {level.upper()}\n"
            body += f"- Score: {score:.2f}\n\n"
        
        return body
    
    def _generate_daily_recommendations(
        self,
        avg_conf: float,
        avg_risk: float,
        agg_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate daily recommendations"""
        recs = []
        
        if avg_conf < 0.6:
            recs.append("Low average confidence - Consider reviewing decision criteria")
        
        if avg_risk > 0.6:
            recs.append("Elevated average risk - Reduce aggressive actions")
        
        if agg_data and agg_data.get('should_throttle'):
            recs.append("System aggressiveness high - Implement throttling")
        
        return recs
    
    def _generate_daily_alerts(
        self,
        decisions: List[Any],
        agg_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate daily alerts"""
        alerts = []
        
        high_risk_count = sum(1 for d in decisions if d.risk_score > 0.7)
        if high_risk_count > 0:
            alerts.append(f"{high_risk_count} high-risk decision(s) detected")
        
        if agg_data and agg_data.get('level') == 'danger':
            alerts.append("System in DANGER zone - Immediate action required")
        
        return alerts
    
    def _generate_risk_alert_summary(self, risk_data: Dict[str, Any], severity: str) -> str:
        """Generate risk alert summary"""
        risk_type = risk_data.get('type', 'unknown')
        score = risk_data.get('score', 0.0)
        return f"{severity.upper()} severity {risk_type} risk detected with score {score:.2f}. Immediate attention recommended."
    
    def _generate_risk_alert_body(self, risk_data: Dict[str, Any]) -> str:
        """Generate risk alert body"""
        body = "## Risk Details\n\n"
        for key, value in risk_data.items():
            if key not in ['type', 'score', 'recommendations']:
                body += f"- **{key}:** {value}\n"
        return body
    
    def _generate_system_status_summary(
        self,
        agg_score: Any,
        recent_count: int,
        metrics: Dict[str, Any]
    ) -> str:
        """Generate system status summary"""
        if agg_score:
            level = agg_score.level.value
            score = agg_score.global_score
            summary = f"System operating at {level.upper()} aggressiveness level ({score:.2f}). "
        else:
            summary = "System status: Not evaluated. "
        
        summary += f"{recent_count} decisions made in last hour. "
        health = metrics.get('health', 'unknown')
        summary += f"Overall health: {health}."
        
        return summary
    
    def _generate_system_status_body(
        self,
        agg_score: Any,
        recent_decisions: List[Any],
        metrics: Dict[str, Any]
    ) -> str:
        """Generate system status body"""
        body = "## Current System State\n\n"
        
        if agg_score:
            body += f"### Aggressiveness Breakdown:\n"
            body += f"- Velocity: {agg_score.velocity_score:.2f}\n"
            body += f"- Concentration: {agg_score.concentration_score:.2f}\n"
            body += f"- Pattern Repetition: {agg_score.pattern_repetition_score:.2f}\n"
            body += f"- Multi-Account: {agg_score.multi_account_score:.2f}\n"
            body += f"- Volume: {agg_score.volume_vs_baseline_score:.2f}\n\n"
        
        body += f"### Recent Activity:\n"
        body += f"- Decisions (1h): {len(recent_decisions)}\n"
        
        return body
