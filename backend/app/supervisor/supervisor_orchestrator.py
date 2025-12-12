"""
SPRINT 10 - Global Supervisor Layer
Module 5: Supervisor Orchestrator - Orquestador Principal

Coordina todo el flujo de supervisión:
Summary → GPT → Gemini → Decision

Maneja fallbacks, logging, telemetry y excepciones.
Es la interfaz principal que usa el Orchestrator.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from .supervisor_contract import (
    SupervisionInput,
    SupervisionOutput,
    SummaryOutput,
    GPTAnalysis,
    ValidationResult,
    ValidationStatus,
    SupervisorConfig,
    create_default_config,
)
from .global_summary_generator import GlobalSummaryGenerator
from .gpt_supervisor import GPTSupervisor
from .gemini_validator import GeminiValidator


# Configurar logging
logger = logging.getLogger(__name__)


class SupervisorOrchestrator:
    """
    Orquestador principal del Supervisor Layer.
    
    Responsibilities:
    - Coordinar Summary → GPT → Gemini
    - Manejar timeouts y errores
    - Implementar fallback strategies
    - Logging y telemetry
    - Proporcionar interfaz unificada
    
    Usage:
        orchestrator = SupervisorOrchestrator(config)
        result = orchestrator.supervise(supervision_input)
        
        if result.final_approval:
            # Proceder con acción
        else:
            # Rechazar o ajustar
    """
    
    def __init__(self, config: Optional[SupervisorConfig] = None):
        self.config = config or create_default_config()
        
        # Inicializar componentes
        self.summary_generator = GlobalSummaryGenerator(
            config={
                "include_metadata": True,
                "detail_level": "detailed",
            }
        )
        
        self.gpt_supervisor = GPTSupervisor(
            config={
                "model": self.config.gpt_model,
                "temperature": self.config.gpt_temperature,
                "simulation_mode": True,  # TODO: Change to False in production
            }
        )
        
        self.gemini_validator = GeminiValidator(config=self.config)
        
        # Fallback strategy
        self.enable_fallback = self.config.enable_fallback
        self.fallback_strategy = self.config.fallback_strategy
        
        # Timeouts
        self.summary_timeout = self.config.summary_timeout_seconds
        self.gpt_timeout = self.config.gpt_timeout_seconds
        self.gemini_timeout = self.config.gemini_timeout_seconds
        
        # Logging config
        self.log_all_decisions = self.config.log_all_decisions
        self.log_rejections = self.config.log_rejections
        self.log_adjustments = self.config.log_adjustments
        
        # Telemetry
        self.telemetry_enabled = True
        self.telemetry_data = []
    
    def supervise(self, supervision_input: SupervisionInput) -> SupervisionOutput:
        """
        Ejecuta el flujo completo de supervisión.
        
        Flow:
        1. Generate Summary (E2B)
        2. GPT Analysis
        3. Gemini Validation
        4. Make final decision
        5. Return result
        
        Args:
            supervision_input: Input con decisiones, acciones, métricas, etc.
            
        Returns:
            SupervisionOutput con decisión final y explicación
        """
        start_time = time.time()
        components_executed = []
        
        try:
            # ==============================================================
            # STEP 1: Generate Summary
            # ==============================================================
            
            logger.info(f"[Supervisor] Starting supervision: {supervision_input.supervision_id}")
            
            summary = self._execute_with_timeout(
                func=self.summary_generator.generate_summary,
                args=(supervision_input,),
                timeout=self.summary_timeout,
                component_name="Summary Generator",
                fallback_func=self._fallback_summary
            )
            components_executed.append("summary_generator")
            
            logger.info(f"[Supervisor] Summary generated: {summary.summary_id}")
            
            # ==============================================================
            # STEP 2: GPT Cognitive Analysis
            # ==============================================================
            
            gpt_analysis = self._execute_with_timeout(
                func=self.gpt_supervisor.analyze,
                args=(summary,),
                timeout=self.gpt_timeout,
                component_name="GPT Supervisor",
                fallback_func=lambda: self._fallback_gpt_analysis(summary)
            )
            components_executed.append("gpt_supervisor")
            
            logger.info(f"[Supervisor] GPT analysis completed: {gpt_analysis.analysis_id}")
            
            # ==============================================================
            # STEP 3: Gemini Hard Validation
            # ==============================================================
            
            gemini_validation = self._execute_with_timeout(
                func=self.gemini_validator.validate,
                args=(summary, gpt_analysis),
                timeout=self.gemini_timeout,
                component_name="Gemini Validator",
                fallback_func=lambda: self._fallback_gemini_validation(summary, gpt_analysis)
            )
            components_executed.append("gemini_validator")
            
            logger.info(
                f"[Supervisor] Gemini validation completed: {gemini_validation.validation_id}, "
                f"approved={gemini_validation.approved}"
            )
            
            # ==============================================================
            # STEP 4: Make Final Decision
            # ==============================================================
            
            final_decision = gemini_validation.status
            final_approval = gemini_validation.approved
            
            # ==============================================================
            # STEP 5: Generate Explanation
            # ==============================================================
            
            explanation = self._generate_explanation(
                summary,
                gpt_analysis,
                gemini_validation,
                final_approval
            )
            
            # ==============================================================
            # STEP 6: Logging
            # ==============================================================
            
            if self.log_all_decisions:
                logger.info(f"[Supervisor] Decision: {final_decision.value}, Approval: {final_approval}")
            
            if self.log_rejections and not final_approval:
                logger.warning(
                    f"[Supervisor] REJECTED: {gemini_validation.reason}, "
                    f"Risk Score: {gemini_validation.risk_score:.2f}"
                )
            
            if self.log_adjustments and gemini_validation.required_adjustments:
                logger.info(
                    f"[Supervisor] Adjustments required: {', '.join(gemini_validation.required_adjustments[:3])}"
                )
            
            # ==============================================================
            # STEP 7: Create Output
            # ==============================================================
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            output = SupervisionOutput(
                supervision_id=supervision_input.supervision_id,
                timestamp=datetime.now(),
                summary=summary,
                gpt_analysis=gpt_analysis,
                gemini_validation=gemini_validation,
                final_decision=final_decision,
                final_approval=final_approval,
                explanation=explanation,
                processing_time_ms=processing_time_ms,
                components_executed=components_executed,
                metadata={
                    "config_used": self.config.__dict__,
                    "fallback_enabled": self.enable_fallback,
                }
            )
            
            # ==============================================================
            # STEP 8: Telemetry
            # ==============================================================
            
            if self.telemetry_enabled:
                self._record_telemetry(output)
            
            logger.info(
                f"[Supervisor] Supervision completed in {processing_time_ms:.1f}ms, "
                f"Result: {final_decision.value}"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"[Supervisor] Fatal error in supervision: {e}", exc_info=True)
            
            # Fallback de emergencia
            if self.enable_fallback:
                return self._emergency_fallback(supervision_input, str(e))
            else:
                raise
    
    def _execute_with_timeout(
        self,
        func,
        args: tuple,
        timeout: int,
        component_name: str,
        fallback_func
    ):
        """
        Ejecuta una función con timeout y fallback.
        
        TODO: Implementar timeout real con threading/asyncio si es necesario.
        Por ahora ejecuta directo sin timeout.
        """
        try:
            # En producción, esto debería usar threading.Timer o asyncio.wait_for
            result = func(*args)
            return result
        
        except Exception as e:
            logger.error(f"[Supervisor] {component_name} failed: {e}")
            
            if self.enable_fallback and fallback_func:
                logger.warning(f"[Supervisor] Using fallback for {component_name}")
                return fallback_func()
            else:
                raise
    
    def _fallback_summary(self, supervision_input: SupervisionInput) -> SummaryOutput:
        """Fallback simple para Summary Generator"""
        logger.warning("[Supervisor] Using fallback summary (minimal)")
        
        from uuid import uuid4
        
        return SummaryOutput(
            summary_id=f"fallback_{uuid4().hex[:12]}",
            timestamp=datetime.now(),
            structured_data={
                "timestamp": datetime.now().isoformat(),
                "supervision_id": supervision_input.supervision_id,
                "fallback": True,
                "message": "Summary generation failed, using minimal fallback"
            },
            natural_language_summary="Summary generation failed. Minimal fallback in use.",
            total_decisions=len(supervision_input.decisions),
            total_actions=len(supervision_input.actions),
            total_risks=len(supervision_input.risks),
            total_anomalies=len(supervision_input.anomalies),
            requires_attention=True,
            critical_issues=["SUMMARY_GENERATION_FAILED"],
        )
    
    def _fallback_gpt_analysis(self, summary: SummaryOutput) -> GPTAnalysis:
        """Fallback simple para GPT Supervisor"""
        logger.warning("[Supervisor] Using fallback GPT analysis (conservative)")
        
        from uuid import uuid4
        
        # Análisis conservador: señalar problemas pero no sugerir acciones agresivas
        return GPTAnalysis(
            analysis_id=f"fallback_{uuid4().hex[:12]}",
            timestamp=datetime.now(),
            observations=["GPT analysis failed, using conservative fallback"],
            detected_patterns=[],
            strategic_suggestions=["REQUIRE_HUMAN_REVIEW"],
            risk_signals=["GPT_ANALYSIS_FAILED"],
            recommended_adjustments=["REDUCE_ACTIVITY", "ENABLE_MANUAL_MODE"],
            confidence=0.2,  # Baja confianza
            model_used="fallback",
            reasoning="GPT analysis component failed. Conservative fallback applied.",
        )
    
    def _fallback_gemini_validation(
        self,
        summary: SummaryOutput,
        gpt_analysis: GPTAnalysis
    ) -> ValidationResult:
        """Fallback para Gemini Validator"""
        logger.warning("[Supervisor] Using fallback Gemini validation")
        
        from uuid import uuid4
        
        # Estrategia de fallback según configuración
        if self.fallback_strategy == "conservative":
            # Conservador: rechazar por precaución
            approved = False
            status = ValidationStatus.NEEDS_HUMAN_REVIEW
            reason = "Gemini validation failed, conservative fallback: reject for safety"
            risk_score = 0.9
        
        elif self.fallback_strategy == "permissive":
            # Permisivo: aprobar con advertencia
            approved = True
            status = ValidationStatus.APPROVED
            reason = "Gemini validation failed, permissive fallback: approved with caution"
            risk_score = 0.5
        
        else:  # "reject_all"
            # Rechazar todo
            approved = False
            status = ValidationStatus.REJECTED
            reason = "Gemini validation failed, reject_all fallback"
            risk_score = 1.0
        
        return ValidationResult(
            validation_id=f"fallback_{uuid4().hex[:12]}",
            timestamp=datetime.now(),
            approved=approved,
            status=status,
            reason=reason,
            risk_score=risk_score,
            risk_breakdown={"fallback_mode": risk_score},
            required_adjustments=["REVIEW_SYSTEM_HEALTH"],
            violated_rules=["GEMINI_VALIDATION_FAILED"],
            model_used="fallback",
            validation_rules_applied=["fallback_strategy"],
        )
    
    def _emergency_fallback(
        self,
        supervision_input: SupervisionInput,
        error_message: str
    ) -> SupervisionOutput:
        """Fallback de emergencia si todo falla"""
        logger.error(f"[Supervisor] EMERGENCY FALLBACK activated: {error_message}")
        
        from uuid import uuid4
        
        # Crear componentes mínimos
        summary = self._fallback_summary(supervision_input)
        gpt_analysis = self._fallback_gpt_analysis(summary)
        gemini_validation = self._fallback_gemini_validation(summary, gpt_analysis)
        
        return SupervisionOutput(
            supervision_id=supervision_input.supervision_id,
            timestamp=datetime.now(),
            summary=summary,
            gpt_analysis=gpt_analysis,
            gemini_validation=gemini_validation,
            final_decision=ValidationStatus.NEEDS_HUMAN_REVIEW,
            final_approval=False,
            explanation=(
                f"EMERGENCY FALLBACK: Supervision pipeline failed with error: {error_message}. "
                "All operations suspended pending human review."
            ),
            processing_time_ms=0.0,
            components_executed=["emergency_fallback"],
            metadata={
                "emergency": True,
                "error": error_message,
            }
        )
    
    def _generate_explanation(
        self,
        summary: SummaryOutput,
        gpt_analysis: GPTAnalysis,
        gemini_validation: ValidationResult,
        final_approval: bool
    ) -> str:
        """Genera explicación completa de la decisión"""
        
        lines = []
        
        lines.append("=== SUPERVISION DECISION ===")
        lines.append("")
        
        # Decision
        decision_emoji = "✅" if final_approval else "❌"
        lines.append(f"{decision_emoji} DECISION: {gemini_validation.status.value.upper()}")
        lines.append(f"Risk Score: {gemini_validation.risk_score:.2f}")
        lines.append(f"Reason: {gemini_validation.reason}")
        lines.append("")
        
        # Summary stats
        lines.append("SYSTEM SUMMARY:")
        lines.append(f"  Decisions: {summary.total_decisions}")
        lines.append(f"  Actions: {summary.total_actions}")
        lines.append(f"  Risks: {summary.total_risks}")
        lines.append(f"  Anomalies: {summary.total_anomalies}")
        if summary.critical_issues:
            lines.append(f"  Critical Issues: {', '.join(summary.critical_issues[:2])}")
        lines.append("")
        
        # GPT insights
        lines.append("GPT COGNITIVE ANALYSIS:")
        if gpt_analysis.observations:
            lines.append(f"  Key Observations: {len(gpt_analysis.observations)}")
        if gpt_analysis.detected_patterns:
            lines.append(f"  Patterns Detected: {len(gpt_analysis.detected_patterns)}")
        if gpt_analysis.risk_signals:
            lines.append(f"  Risk Signals: {len(gpt_analysis.risk_signals)}")
            for signal in gpt_analysis.risk_signals[:2]:
                lines.append(f"    - {signal}")
        lines.append(f"  Confidence: {gpt_analysis.confidence:.2f}")
        lines.append("")
        
        # Gemini validation
        lines.append("GEMINI VALIDATION:")
        if gemini_validation.violated_rules:
            lines.append(f"  Violated Rules: {len(gemini_validation.violated_rules)}")
            for rule in gemini_validation.violated_rules[:3]:
                lines.append(f"    - {rule}")
        if gemini_validation.required_adjustments:
            lines.append(f"  Required Adjustments: {len(gemini_validation.required_adjustments)}")
            for adj in gemini_validation.required_adjustments[:3]:
                lines.append(f"    - {adj}")
        lines.append("")
        
        # Recommended actions
        if not final_approval:
            lines.append("RECOMMENDED ACTIONS:")
            if gemini_validation.required_adjustments:
                for adj in gemini_validation.required_adjustments[:5]:
                    lines.append(f"  - {adj}")
            else:
                lines.append("  - AWAIT_HUMAN_REVIEW")
        
        return "\n".join(lines)
    
    def _record_telemetry(self, output: SupervisionOutput):
        """Registra telemetría para análisis posterior"""
        telemetry_record = {
            "timestamp": output.timestamp.isoformat(),
            "supervision_id": output.supervision_id,
            "final_approval": output.final_approval,
            "final_decision": output.final_decision.value,
            "risk_score": output.gemini_validation.risk_score,
            "processing_time_ms": output.processing_time_ms,
            "components_executed": output.components_executed,
            "total_decisions": output.summary.total_decisions,
            "total_actions": output.summary.total_actions,
            "total_risks": output.summary.total_risks,
            "gpt_confidence": output.gpt_analysis.confidence,
            "violated_rules_count": len(output.gemini_validation.violated_rules),
        }
        
        self.telemetry_data.append(telemetry_record)
        
        # Limitar tamaño del buffer
        if len(self.telemetry_data) > 1000:
            self.telemetry_data = self.telemetry_data[-1000:]
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de telemetría"""
        if not self.telemetry_data:
            return {"message": "No telemetry data available"}
        
        total = len(self.telemetry_data)
        approved = sum(1 for t in self.telemetry_data if t["final_approval"])
        rejected = total - approved
        
        avg_risk_score = sum(t["risk_score"] for t in self.telemetry_data) / total
        avg_processing_time = sum(t["processing_time_ms"] for t in self.telemetry_data) / total
        
        return {
            "total_supervisions": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total if total > 0 else 0,
            "avg_risk_score": avg_risk_score,
            "avg_processing_time_ms": avg_processing_time,
            "recent_data": self.telemetry_data[-10:],
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_supervisor_orchestrator(config: Optional[SupervisorConfig] = None) -> SupervisorOrchestrator:
    """Helper para crear un SupervisorOrchestrator"""
    return SupervisorOrchestrator(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SupervisorOrchestrator",
    "create_supervisor_orchestrator",
]
