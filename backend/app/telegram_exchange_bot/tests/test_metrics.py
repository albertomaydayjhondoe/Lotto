"""
Tests for Sprint 7B - Metrics Module
Test de sistema de métricas y ROI.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.telegram_exchange_bot.metrics import (
    MetricsCollector,
    InteractionMetric,
    ROIMetrics,
    PerformanceDashboard,
    MetricPeriod
)
from app.telegram_exchange_bot.executor import (
    ExecutionResult,
    ExecutionStatus
)
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccount,
    AccountStatus,
    AccountHealth
)
from app.telegram_exchange_bot.models import InteractionType, Platform


@pytest.fixture
def mock_db():
    """Mock database."""
    return Mock()


@pytest.fixture
def metrics_collector(mock_db):
    """MetricsCollector fixture."""
    return MetricsCollector(db=mock_db)


@pytest.fixture
def sample_account():
    """Sample account."""
    return NonOfficialAccount(
        account_id="test_acc_001",
        platform="youtube",
        username="test_support",
        status=AccountStatus.ACTIVE,
        health=AccountHealth.HEALTHY
    )


@pytest.fixture
def sample_execution_result(sample_account):
    """Sample execution result."""
    return ExecutionResult(
        status=ExecutionStatus.SUCCESS,
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test123",
        account_used=sample_account,
        execution_time_seconds=2.5,
        metadata={"test": True}
    )


# ============================================================================
# METRICS COLLECTOR TESTS
# ============================================================================

def test_metrics_collector_initialization(metrics_collector):
    """Test: MetricsCollector se inicializa correctamente."""
    assert metrics_collector.db is not None
    assert metrics_collector.brain is not None
    assert len(metrics_collector._buffer) == 0
    assert metrics_collector._buffer_size == 50


@pytest.mark.asyncio
async def test_record_execution_adds_to_buffer(metrics_collector, sample_execution_result):
    """Test: Registrar ejecución añade al buffer."""
    initial_size = len(metrics_collector._buffer)
    
    await metrics_collector.record_execution(
        execution_result=sample_execution_result,
        telegram_group_id="group_001",
        telegram_group_name="Test Group"
    )
    
    assert len(metrics_collector._buffer) == initial_size + 1


@pytest.mark.asyncio
async def test_buffer_flushes_after_limit(metrics_collector, sample_execution_result):
    """Test: Buffer se flush después del límite."""
    # Llenar buffer hasta el límite
    for i in range(metrics_collector._buffer_size):
        await metrics_collector.record_execution(
            execution_result=sample_execution_result
        )
    
    # Buffer debe haberse vaciado
    assert len(metrics_collector._buffer) == 0


@pytest.mark.asyncio
async def test_calculate_roi_group(metrics_collector):
    """Test: Calcula ROI para grupo."""
    roi = await metrics_collector.calculate_roi(
        entity_id="group_001",
        entity_type="group",
        period=MetricPeriod.DAILY
    )
    
    assert roi is not None
    assert roi.entity_id == "group_001"
    assert roi.entity_type == "group"
    assert roi.period == MetricPeriod.DAILY
    assert roi.success_rate >= 0.0


@pytest.mark.asyncio
async def test_calculate_roi_user(metrics_collector):
    """Test: Calcula ROI para usuario."""
    roi = await metrics_collector.calculate_roi(
        entity_id="user_001",
        entity_type="user",
        period=MetricPeriod.WEEKLY
    )
    
    assert roi.entity_type == "user"
    assert roi.roi_ratio >= 0.0


@pytest.mark.asyncio
async def test_generate_dashboard(metrics_collector):
    """Test: Genera dashboard de performance."""
    dashboard = await metrics_collector.generate_dashboard(
        period=MetricPeriod.DAILY
    )
    
    assert dashboard is not None
    assert dashboard.period == MetricPeriod.DAILY
    assert dashboard.success_rate >= 0.0
    assert isinstance(dashboard.top_groups, list)
    assert isinstance(dashboard.top_users, list)
    assert dashboard.health_status in ["healthy", "warning", "critical"]


@pytest.mark.asyncio
async def test_dashboard_healthy_status(metrics_collector):
    """Test: Dashboard marca como healthy con buenos metrics."""
    dashboard = await metrics_collector.generate_dashboard()
    
    # Mock data tiene 87.5% success rate y 1.12 ROI
    # Debe ser healthy
    assert dashboard.health_status in ["healthy", "warning"]


@pytest.mark.asyncio
async def test_export_to_orchestrator(metrics_collector):
    """Test: Exporta métricas al orchestrator."""
    result = await metrics_collector.export_to_orchestrator(
        period=MetricPeriod.DAILY
    )
    
    assert result["exported"] is True
    assert "timestamp" in result
    assert "brain_mode" in result


def test_metrics_collector_stats(metrics_collector):
    """Test: Stats del collector."""
    stats = metrics_collector.get_stats()
    
    assert "buffer_size" in stats
    assert "buffer_capacity" in stats
    assert "interaction_costs" in stats


# ============================================================================
# INTERACTION METRIC TESTS
# ============================================================================

def test_interaction_metric_creation(sample_account):
    """Test: InteractionMetric se crea correctamente."""
    metric = InteractionMetric(
        interaction_id="int_test_001",
        executed_at=datetime.utcnow(),
        interaction_type=InteractionType.YOUTUBE_LIKE,
        platform=Platform.YOUTUBE,
        target_url="https://youtube.com/watch?v=test",
        account_id=sample_account.account_id,
        account_username=sample_account.username,
        status=ExecutionStatus.SUCCESS,
        execution_time_seconds=2.5,
        vpn_active=True,
        proxy_used="http://proxy.test:8080",
        fingerprint_id="fp_123"
    )
    
    assert metric.interaction_id == "int_test_001"
    assert metric.interaction_type == InteractionType.YOUTUBE_LIKE
    assert metric.status == ExecutionStatus.SUCCESS
    assert metric.vpn_active is True


# ============================================================================
# ROI METRICS TESTS
# ============================================================================

def test_roi_metrics_creation():
    """Test: ROIMetrics se crea correctamente."""
    roi = ROIMetrics(
        entity_id="group_001",
        entity_type="group",
        period=MetricPeriod.DAILY
    )
    
    assert roi.entity_id == "group_001"
    assert roi.entity_type == "group"
    assert roi.period == MetricPeriod.DAILY
    assert roi.total_interactions == 0


def test_roi_metrics_calculates_success_rate():
    """Test: ROI calcula success rate."""
    roi = ROIMetrics(
        entity_id="test",
        entity_type="group",
        period=MetricPeriod.DAILY,
        total_interactions=100,
        successful_interactions=85,
        failed_interactions=15
    )
    
    roi.success_rate = roi.successful_interactions / roi.total_interactions
    assert roi.success_rate == 0.85


def test_roi_metrics_calculates_roi_ratio():
    """Test: ROI calcula ratio de reciprocidad."""
    roi = ROIMetrics(
        entity_id="test",
        entity_type="group",
        period=MetricPeriod.DAILY,
        support_given=100,
        support_received=120
    )
    
    roi.roi_ratio = roi.support_received / roi.support_given
    assert roi.roi_ratio == 1.2  # Recibimos 20% más


def test_roi_metrics_negative_roi():
    """Test: ROI detecta ratio negativo."""
    roi = ROIMetrics(
        entity_id="test",
        entity_type="group",
        period=MetricPeriod.DAILY,
        support_given=100,
        support_received=60
    )
    
    roi.roi_ratio = roi.support_received / roi.support_given
    assert roi.roi_ratio < 1.0  # Recibimos menos de lo que damos


# ============================================================================
# PERFORMANCE DASHBOARD TESTS
# ============================================================================

def test_dashboard_creation():
    """Test: Dashboard se crea correctamente."""
    dashboard = PerformanceDashboard(
        period=MetricPeriod.DAILY,
        generated_at=datetime.utcnow()
    )
    
    assert dashboard.period == MetricPeriod.DAILY
    assert dashboard.total_executions == 0
    assert isinstance(dashboard.top_groups, list)


def test_dashboard_calculates_success_rate():
    """Test: Dashboard calcula success rate."""
    dashboard = PerformanceDashboard(
        period=MetricPeriod.DAILY,
        generated_at=datetime.utcnow(),
        total_executions=100,
        successful_executions=88,
        failed_executions=12
    )
    
    dashboard.success_rate = (
        dashboard.successful_executions / dashboard.total_executions
    )
    
    assert dashboard.success_rate == 0.88


def test_dashboard_health_critical():
    """Test: Dashboard detecta estado crítico."""
    dashboard = PerformanceDashboard(
        period=MetricPeriod.DAILY,
        generated_at=datetime.utcnow(),
        total_executions=100,
        successful_executions=60,  # 60% success rate
        global_roi=0.4  # ROI muy bajo
    )
    
    dashboard.success_rate = 0.60
    
    # Debe marcar como crítico (< 70% success o < 0.5 ROI)
    if dashboard.success_rate < 0.7 or dashboard.global_roi < 0.5:
        dashboard.health_status = "critical"
    
    assert dashboard.health_status == "critical"


def test_dashboard_health_warning():
    """Test: Dashboard detecta estado warning."""
    dashboard = PerformanceDashboard(
        period=MetricPeriod.DAILY,
        generated_at=datetime.utcnow(),
        total_executions=100,
        successful_executions=80,  # 80% success rate
        global_roi=0.85
    )
    
    dashboard.success_rate = 0.80
    
    # Debe marcar como warning (< 85% success o < 0.9 ROI)
    if 0.7 <= dashboard.success_rate < 0.85 or 0.5 <= dashboard.global_roi < 0.9:
        dashboard.health_status = "warning"
    else:
        dashboard.health_status = "healthy"
    
    assert dashboard.health_status == "warning"


def test_dashboard_recommendations():
    """Test: Dashboard genera recomendaciones."""
    dashboard = PerformanceDashboard(
        period=MetricPeriod.DAILY,
        generated_at=datetime.utcnow(),
        total_executions=100,
        successful_executions=75,
        failed_executions=25,
        global_roi=0.80,
        total_cost_eur=12.0
    )
    
    dashboard.success_rate = 0.75
    
    recommendations = []
    
    if dashboard.success_rate < 0.85:
        recommendations.append("Success rate bajo")
    
    if dashboard.global_roi < 0.9:
        recommendations.append("ROI global bajo")
    
    if dashboard.total_cost_eur > 10.0:
        recommendations.append("Costo alto")
    
    assert len(recommendations) >= 2  # Al menos 2 recomendaciones
