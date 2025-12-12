"""
Test Content Engine Orchestrator
Tests unitarios para el orquestador principal.
"""

import pytest
from app.content_engine.orchestrator import ContentEngineOrchestrator
from app.content_engine.models import ContentAnalysisRequest
from app.content_engine.config import ContentEngineConfig


@pytest.fixture
def config():
    """Config de test con límites reducidos."""
    return ContentEngineConfig(
        llm_model="gpt-4o-mini",
        max_cost_per_request=0.10,
        enable_telemetry=True
    )


@pytest.fixture
def orchestrator(config):
    """Orchestrator de test."""
    return ContentEngineOrchestrator(config)


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test: Orchestrator se inicializa correctamente."""
    assert orchestrator is not None
    assert orchestrator.config is not None
    assert orchestrator.video_analyzer is not None
    assert orchestrator.hook_generator is not None


@pytest.mark.asyncio
async def test_analyze_and_generate_success(orchestrator):
    """Test: Análisis completo ejecuta exitosamente."""
    request = ContentAnalysisRequest(
        video_id="test_video_123",
        target_platform="instagram",
        generate_hooks=True,
        generate_captions=True
    )
    
    response = await orchestrator.analyze_and_generate(request)
    
    assert response.success is True
    assert response.video_id == "test_video_123"
    assert response.video_analysis is not None
    assert response.trend_analysis is not None
    assert response.generated_content is not None
    assert len(response.generated_content.hooks) > 0
    assert len(response.generated_content.captions) > 0
    assert response.total_cost_eur >= 0.0


@pytest.mark.asyncio
async def test_analyze_without_generation(orchestrator):
    """Test: Análisis sin generación de contenido."""
    request = ContentAnalysisRequest(
        video_id="test_video_456",
        generate_hooks=False,
        generate_captions=False
    )
    
    response = await orchestrator.analyze_and_generate(request)
    
    assert response.success is True
    assert response.video_analysis is not None
    assert len(response.generated_content.hooks) == 0
    assert len(response.generated_content.captions) == 0


@pytest.mark.asyncio
async def test_metrics_collection(orchestrator):
    """Test: Métricas se recolectan correctamente."""
    request = ContentAnalysisRequest(
        video_id="test_metrics",
        generate_hooks=True
    )
    
    response = await orchestrator.analyze_and_generate(request)
    
    assert response.metrics is not None
    assert response.metrics.success is True
    assert response.metrics.execution_time_ms > 0
    assert response.metrics.video_id == "test_metrics"


@pytest.mark.asyncio
async def test_get_metrics_summary(orchestrator):
    """Test: Resumen de métricas agregadas."""
    # Ejecutar varias requests
    for i in range(3):
        request = ContentAnalysisRequest(
            video_id=f"test_video_{i}",
            generate_hooks=True
        )
        await orchestrator.analyze_and_generate(request)
    
    summary = await orchestrator.get_metrics_summary()
    
    assert summary["total_requests"] == 3
    assert summary["successful_requests"] == 3
    assert summary["success_rate"] == 1.0
    assert summary["total_cost_eur"] >= 0.0


@pytest.mark.asyncio
async def test_cost_limits_check(orchestrator):
    """Test: Verificación de límites de coste."""
    cost_limits = await orchestrator.check_cost_limits()
    
    assert "daily" in cost_limits
    assert "monthly" in cost_limits
    assert cost_limits["daily"]["limit"] == orchestrator.config.max_daily_cost
    assert cost_limits["monthly"]["limit"] == orchestrator.config.max_monthly_cost
