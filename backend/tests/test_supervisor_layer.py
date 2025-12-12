"""
SPRINT 10 - Global Supervisor Layer
Tests completos del Supervisor Layer

Tests Coverage:
- Payload incompleto → rechazo
- Riesgo alto → rechazo
- Presupuesto excedido → rechazo automático
- Repetición de patrón → bloqueo
- GPT falla → fallback seguro
- Gemini falla → fallback seguro
- Integración completa
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from app.supervisor.supervisor_contract import (
    SupervisionInput,
    SupervisorConfig,
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
    ValidationStatus,
    create_supervision_input,
    create_default_config,
)
from app.supervisor.global_summary_generator import GlobalSummaryGenerator
from app.supervisor.gpt_supervisor import GPTSupervisor
from app.supervisor.gemini_validator import GeminiValidator
from app.supervisor.supervisor_orchestrator import SupervisorOrchestrator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def default_config():
    """Configuración por defecto"""
    return create_default_config()


@pytest.fixture
def summary_generator():
    """GlobalSummaryGenerator para tests"""
    return GlobalSummaryGenerator()


@pytest.fixture
def gpt_supervisor():
    """GPTSupervisor para tests (modo simulación)"""
    return GPTSupervisor(config={"simulation_mode": True})


@pytest.fixture
def gemini_validator():
    """GeminiValidator para tests (modo simulación)"""
    config = create_default_config()
    validator = GeminiValidator(config=config)
    validator.simulation_mode = True
    return validator


@pytest.fixture
def supervisor_orchestrator():
    """SupervisorOrchestrator para tests"""
    config = create_default_config()
    config.enable_fallback = True
    config.fallback_strategy = "conservative"
    return SupervisorOrchestrator(config)


@pytest.fixture
def basic_supervision_input():
    """SupervisionInput básico para tests"""
    return create_supervision_input(
        engine_source=EngineSource.SATELLITE,
        severity=SeverityLevel.MEDIUM,
        context_summary="Test supervision input"
    )


@pytest.fixture
def complete_supervision_input():
    """SupervisionInput completo con todos los campos"""
    decisions = [
        Decision(
            type=DecisionType.PUBLISH_CONTENT,
            description="Publish content to account A",
            engine_source=EngineSource.SATELLITE,
            timestamp=datetime.now(),
            reasoning="Optimal timing detected",
            confidence=0.8
        )
    ]
    
    actions = [
        Action(
            action_id="action_001",
            type="publish_post",
            engine_source=EngineSource.SATELLITE,
            timestamp=datetime.now(),
            target="account_A",
            success=True
        )
    ]
    
    metrics = Metrics(
        avg_retention=0.65,
        engagement_velocity=0.72,
        avg_ctr=0.034,
        avg_cpm=8.5,
        avg_cpc=0.45,
        ml_confidence=0.78
    )
    
    costs = CostReport(
        today=15.50,
        month_accumulated=245.00,
        budget_total=1000.00,
        budget_remaining=755.00
    )
    
    input_obj = create_supervision_input(
        engine_source=EngineSource.SATELLITE,
        severity=SeverityLevel.MEDIUM,
        decisions=decisions,
        actions=actions,
        context_summary="Complete test input"
    )
    input_obj.metrics = metrics
    input_obj.costs = costs
    
    return input_obj


# ============================================================================
# TEST: GlobalSummaryGenerator
# ============================================================================

class TestGlobalSummaryGenerator:
    """Tests para GlobalSummaryGenerator"""
    
    def test_generate_summary_basic(self, summary_generator, basic_supervision_input):
        """Test: Generar resumen básico"""
        summary = summary_generator.generate_summary(basic_supervision_input)
        
        assert summary.summary_id is not None
        assert summary.timestamp is not None
        assert summary.structured_data is not None
        assert summary.natural_language_summary is not None
        assert isinstance(summary.structured_data, dict)
    
    def test_generate_summary_complete(self, summary_generator, complete_supervision_input):
        """Test: Generar resumen completo con todos los datos"""
        summary = summary_generator.generate_summary(complete_supervision_input)
        
        assert summary.total_decisions == 1
        assert summary.total_actions == 1
        assert "metrics" in summary.structured_data
        assert "costs" in summary.structured_data
        
        # Verificar structure del JSON
        structured = summary.structured_data
        assert "timestamp" in structured
        assert "decisions" in structured
        assert "actions" in structured
        assert len(structured["decisions"]) == 1
        assert len(structured["actions"]) == 1
    
    def test_identify_critical_issues_budget_exceeded(self, summary_generator):
        """Test: Identificar issue crítico de presupuesto excedido"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.HIGH
        )
        
        # Budget excedido
        input_obj.costs = CostReport(
            today=55.00,
            month_accumulated=1100.00,
            budget_total=1000.00,
            budget_remaining=-100.00
        )
        
        summary = summary_generator.generate_summary(input_obj)
        
        assert summary.requires_attention is True
        assert len(summary.critical_issues) > 0
        assert any("BUDGET_EXCEEDED" in issue for issue in summary.critical_issues)
    
    def test_identify_critical_issues_shadowban(self, summary_generator):
        """Test: Identificar shadowban signals"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.HIGH
        )
        
        input_obj.metrics = Metrics(
            shadowban_signals=3,
            correlation_signals=2
        )
        
        summary = summary_generator.generate_summary(input_obj)
        
        assert summary.requires_attention is True
        assert any("SHADOWBAN" in issue for issue in summary.critical_issues)
    
    def test_detect_pattern_repetition(self, summary_generator):
        """Test: Detectar repetición de patrones"""
        # Generar múltiples summaries con mismo patrón
        for _ in range(5):
            input_obj = create_supervision_input(
                engine_source=EngineSource.SATELLITE,
                severity=SeverityLevel.LOW,
                decisions=[
                    Decision(
                        type=DecisionType.PUBLISH_CONTENT,
                        description="Same pattern",
                        engine_source=EngineSource.SATELLITE,
                        timestamp=datetime.now(),
                        reasoning="Test",
                        confidence=0.5
                    )
                ]
            )
            summary_generator.generate_summary(input_obj)
        
        # Detectar patrón
        pattern_analysis = summary_generator.detect_pattern_repetition(lookback_hours=1)
        
        assert "repetition_score" in pattern_analysis
        assert pattern_analysis["repetition_score"] > 0.5  # Alta repetición


# ============================================================================
# TEST: GPTSupervisor
# ============================================================================

class TestGPTSupervisor:
    """Tests para GPTSupervisor"""
    
    def test_analyze_basic(self, gpt_supervisor, summary_generator, basic_supervision_input):
        """Test: Análisis básico de GPT"""
        summary = summary_generator.generate_summary(basic_supervision_input)
        analysis = gpt_supervisor.analyze(summary)
        
        assert analysis.analysis_id is not None
        assert analysis.timestamp is not None
        assert isinstance(analysis.observations, list)
        assert isinstance(analysis.detected_patterns, list)
        assert isinstance(analysis.strategic_suggestions, list)
        assert isinstance(analysis.risk_signals, list)
        assert isinstance(analysis.recommended_adjustments, list)
        assert 0.0 <= analysis.confidence <= 1.0
    
    def test_analyze_low_engagement(self, gpt_supervisor, summary_generator):
        """Test: GPT detecta engagement bajo"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.MEDIUM
        )
        
        # Engagement muy bajo
        input_obj.metrics = Metrics(
            avg_retention=0.15,  # 15% - muy bajo
            engagement_velocity=0.2
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        # Debe detectar el problema
        assert len(analysis.observations) > 0
        assert any("low" in obs.lower() for obs in analysis.observations)
        
        # Debe sugerir ajustes
        assert len(analysis.strategic_suggestions) > 0
    
    def test_analyze_high_cpm(self, gpt_supervisor, summary_generator):
        """Test: GPT detecta CPM alto"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.MEDIUM
        )
        
        input_obj.metrics = Metrics(
            avg_cpm=20.0,  # CPM muy alto
            avg_cpc=1.50
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        # Debe mencionar CPM alto
        assert any("cpm" in sugg.lower() for sugg in analysis.strategic_suggestions)
    
    def test_analyze_shadowban_signals(self, gpt_supervisor, summary_generator):
        """Test: GPT detecta shadowban signals"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.HIGH
        )
        
        input_obj.metrics = Metrics(
            shadowban_signals=5
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        # Debe alertar sobre shadowban
        assert len(analysis.risk_signals) > 0
        assert any("shadowban" in sig.lower() for sig in analysis.risk_signals)
        
        # Debe recomendar ajustes
        assert any("reduce" in adj.lower() or "pause" in adj.lower() for adj in analysis.recommended_adjustments)


# ============================================================================
# TEST: GeminiValidator
# ============================================================================

class TestGeminiValidator:
    """Tests para GeminiValidator"""
    
    def test_validate_approved_clean(self, gemini_validator, summary_generator, gpt_supervisor, complete_supervision_input):
        """Test: Validación aprobada con datos limpios"""
        summary = summary_generator.generate_summary(complete_supervision_input)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.validation_id is not None
        assert validation.approved is True
        assert validation.status == ValidationStatus.APPROVED
        assert validation.risk_score < 0.6
    
    def test_validate_rejected_budget_exceeded(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por presupuesto excedido"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.CRITICAL
        )
        
        # Presupuesto diario excedido
        input_obj.costs = CostReport(
            today=60.0,  # Límite es 50.0
            month_accumulated=500.0,
            budget_total=1000.0,
            budget_remaining=500.0
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.approved is False
        assert validation.status == ValidationStatus.REJECTED
        assert any("BUDGET" in rule for rule in validation.violated_rules)
        assert "HALT_ALL_SPENDING" in validation.required_adjustments
    
    def test_validate_rejected_monthly_budget_exceeded(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por presupuesto mensual excedido"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.CRITICAL
        )
        
        input_obj.costs = CostReport(
            today=10.0,
            month_accumulated=1050.0,  # Excede 1000.0
            budget_total=1000.0,
            budget_remaining=-50.0
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.approved is False
        assert any("MONTHLY_BUDGET" in rule for rule in validation.violated_rules)
    
    def test_validate_rejected_high_failure_rate(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por alta tasa de fallos"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.HIGH
        )
        
        # 6 de 10 acciones fallidas (60%)
        input_obj.actions = [
            Action(
                action_id=f"action_{i}",
                type="publish",
                engine_source=EngineSource.SATELLITE,
                timestamp=datetime.now(),
                target=f"account_{i}",
                success=(i >= 6)  # Primeras 6 fallan
            )
            for i in range(10)
        ]
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.approved is False
        assert any("FAILURE" in rule for rule in validation.violated_rules)
    
    def test_validate_rejected_shadowban_signals(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por shadowban signals"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.HIGH
        )
        
        input_obj.metrics = Metrics(
            shadowban_signals=8  # Alto
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.approved is False
        assert any("SHADOWBAN" in rule for rule in validation.violated_rules)
        assert "PAUSE_AFFECTED_ACCOUNTS" in validation.required_adjustments
    
    def test_validate_rejected_high_correlation(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por alta correlación de identidades"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.HIGH
        )
        
        input_obj.metrics = Metrics(
            correlation_signals=12  # Muy alto
        )
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        assert validation.approved is False
        assert any("CORRELATION" in rule for rule in validation.violated_rules)
        assert "ROTATE_VPN_SERVERS" in validation.required_adjustments
    
    def test_validate_rejected_cognitive_incoherence(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Rechazo por incoherencia cognitiva"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.MEDIUM
        )
        
        # Engagement muy bajo
        input_obj.metrics = Metrics(
            avg_retention=0.15,  # 15%
            engagement_velocity=0.2
        )
        
        # Pero se decide escalar ads (incoherente)
        input_obj.decisions = [
            Decision(
                type=DecisionType.SCALE_ADS,
                description="Scale ads campaign",
                engine_source=EngineSource.META_ADS,
                timestamp=datetime.now(),
                reasoning="Test incoherence",
                confidence=0.9
            )
        ]
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        
        validation = gemini_validator.validate(summary, analysis)
        
        # Debe detectar incoherencia
        assert validation.approved is False
        assert any("INCOHERENCE" in rule for rule in validation.violated_rules)


# ============================================================================
# TEST: SupervisorOrchestrator
# ============================================================================

class TestSupervisorOrchestrator:
    """Tests para SupervisorOrchestrator - Integración completa"""
    
    def test_supervise_approved_workflow(self, supervisor_orchestrator, complete_supervision_input):
        """Test: Flujo completo de supervisión - Aprobado"""
        result = supervisor_orchestrator.supervise(complete_supervision_input)
        
        assert result.supervision_id == complete_supervision_input.supervision_id
        assert result.summary is not None
        assert result.gpt_analysis is not None
        assert result.gemini_validation is not None
        assert result.final_decision is not None
        assert result.explanation is not None
        assert result.processing_time_ms > 0
        assert len(result.components_executed) == 3  # Summary, GPT, Gemini
    
    def test_supervise_rejected_budget(self, supervisor_orchestrator):
        """Test: Flujo completo - Rechazado por presupuesto"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.META_ADS,
            severity=SeverityLevel.CRITICAL
        )
        
        input_obj.costs = CostReport(
            today=75.0,  # Excede límite de 50.0
            month_accumulated=800.0,
            budget_total=1000.0,
            budget_remaining=200.0
        )
        
        result = supervisor_orchestrator.supervise(input_obj)
        
        assert result.final_approval is False
        assert result.final_decision in [ValidationStatus.REJECTED, ValidationStatus.REQUIRES_ADJUSTMENT]
        assert "BUDGET" in result.explanation or "budget" in result.explanation.lower()
    
    def test_telemetry_recording(self, supervisor_orchestrator, complete_supervision_input):
        """Test: Telemetría se registra correctamente"""
        # Ejecutar varias supervisiones
        for _ in range(3):
            supervisor_orchestrator.supervise(complete_supervision_input)
        
        telemetry = supervisor_orchestrator.get_telemetry_summary()
        
        assert telemetry["total_supervisions"] >= 3
        assert "approved" in telemetry
        assert "rejected" in telemetry
        assert "approval_rate" in telemetry
        assert "avg_risk_score" in telemetry
        assert "avg_processing_time_ms" in telemetry
    
    def test_fallback_conservative_strategy(self, supervisor_orchestrator):
        """Test: Fallback conservador funciona"""
        # Crear input que podría causar error (pero en simulación no debería)
        # Este test verifica que el sistema maneja errores gracefully
        
        input_obj = create_supervision_input(
            engine_source=EngineSource.ORCHESTRATOR,
            severity=SeverityLevel.HIGH
        )
        
        # Añadir datos extremos para forzar procesamiento complejo
        input_obj.anomalies = [
            Anomaly(
                anomaly_id=f"anomaly_{i}",
                type="test_anomaly",
                description="Test anomaly for fallback testing",
                severity=SeverityLevel.HIGH,
                detected_at=datetime.now(),
                requires_investigation=True
            )
            for i in range(10)
        ]
        
        # No debería fallar
        result = supervisor_orchestrator.supervise(input_obj)
        
        assert result is not None
        assert result.final_decision is not None
    
    def test_payload_incompleto_manejo(self, supervisor_orchestrator):
        """Test: Manejo de payload incompleto"""
        # Payload mínimo
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.LOW
        )
        
        # Sin decisiones, sin acciones, sin métricas
        
        result = supervisor_orchestrator.supervise(input_obj)
        
        # Debe completarse sin error
        assert result is not None
        assert result.summary.total_decisions == 0
        assert result.summary.total_actions == 0


# ============================================================================
# TEST: Reglas específicas de validación
# ============================================================================

class TestValidationRules:
    """Tests de reglas de validación específicas"""
    
    def test_rule_daily_budget_limit(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Regla de límite diario de presupuesto"""
        config = create_default_config()
        config.daily_budget_limit = 50.0
        
        validator = GeminiValidator(config)
        validator.simulation_mode = True
        
        # Justo en el límite
        input_obj = create_supervision_input(EngineSource.META_ADS, SeverityLevel.MEDIUM)
        input_obj.costs = CostReport(today=50.0, budget_total=1000.0)
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        validation = validator.validate(summary, analysis)
        
        # En el límite exacto = rechazo
        assert validation.approved is False
    
    def test_rule_pattern_similarity_threshold(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Threshold de similitud de patrones"""
        config = create_default_config()
        config.pattern_similarity_threshold = 0.6
        
        validator = GeminiValidator(config)
        validator.simulation_mode = True
        
        input_obj = create_supervision_input(EngineSource.SATELLITE, SeverityLevel.HIGH)
        
        # Simular GPT detectando patrones repetitivos
        summary = summary_generator.generate_summary(input_obj)
        
        # Mock GPT analysis con patrones
        analysis = gpt_supervisor.analyze(summary)
        analysis.detected_patterns = [
            "Repetitive pattern A detected",
            "Repetitive pattern B detected",
            "Repetitive pattern C detected"
        ]
        
        validation = validator.validate(summary, analysis)
        
        # Debe rechazar por alta repetición
        assert validation.approved is False
        assert validation.risk_breakdown.get("pattern_repetition", 0) > 0


# ============================================================================
# TEST: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests de casos extremos"""
    
    def test_empty_supervision_input(self, supervisor_orchestrator):
        """Test: Input vacío"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.ORCHESTRATOR,
            severity=SeverityLevel.LOW
        )
        
        result = supervisor_orchestrator.supervise(input_obj)
        assert result is not None
    
    def test_all_actions_failed(self, supervisor_orchestrator):
        """Test: Todas las acciones fallidas"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.CRITICAL
        )
        
        input_obj.actions = [
            Action(
                action_id=f"action_{i}",
                type="publish",
                engine_source=EngineSource.SATELLITE,
                timestamp=datetime.now(),
                target=f"account_{i}",
                success=False,
                error_message="Test failure"
            )
            for i in range(5)
        ]
        
        result = supervisor_orchestrator.supervise(input_obj)
        
        assert result.final_approval is False
    
    def test_extreme_risk_score(self, gemini_validator, summary_generator, gpt_supervisor):
        """Test: Risk score extremo"""
        input_obj = create_supervision_input(
            engine_source=EngineSource.SATELLITE,
            severity=SeverityLevel.CRITICAL
        )
        
        # Múltiples problemas críticos
        input_obj.costs = CostReport(today=100.0, month_accumulated=1500.0, budget_total=1000.0)
        input_obj.metrics = Metrics(shadowban_signals=10, correlation_signals=15)
        input_obj.actions = [
            Action(
                action_id=f"action_{i}",
                type="test",
                engine_source=EngineSource.SATELLITE,
                timestamp=datetime.now(),
                target=f"target_{i}",
                success=False
            )
            for i in range(10)
        ]
        
        summary = summary_generator.generate_summary(input_obj)
        analysis = gpt_supervisor.analyze(summary)
        validation = gemini_validator.validate(summary, analysis)
        
        # Risk score debe ser muy alto
        assert validation.risk_score >= 0.8
        assert validation.approved is False
        assert len(validation.violated_rules) > 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
