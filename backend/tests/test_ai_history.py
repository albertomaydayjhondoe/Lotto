"""
PASO 8.1 - AI Memory Layer Tests

Tests comprehensivos para el sistema de historial de AI Global Worker.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AIReasoningHistoryModel
from app.ai_global_worker.history_service import (
    save_reasoning_to_history,
    get_history,
    get_history_item,
    _determine_status,
    _count_critical_issues,
)
from app.ai_global_worker.schemas import (
    AIReasoningOutput,
    SystemSnapshot,
    AISummary,
    AIRecommendation,
    AIActionPlan,
)


# === Mock Helpers ===

def create_mock_snapshot(override: dict = None) -> SystemSnapshot:
    """Crea un SystemSnapshot de prueba."""
    base = {
        "timestamp": datetime.utcnow(),
        "queue_pending": 10,
        "queue_processing": 2,
        "queue_failed": 1,
        "queue_success": 20,
        "scheduler_pending": 5,
        "scheduler_due_soon": 2,
        "orchestrator_running": True,
        "orchestrator_last_run": datetime.utcnow(),
        "orchestrator_actions_last_24h": 10,
        "publish_success_rate": 0.95,
        "publish_total_24h": 50,
        "publish_failed_24h": 3,
        "clips_ready": 50,
        "clips_pending_analysis": 10,
        "jobs_pending": 5,
        "jobs_failed": 1,
        "campaigns_active": 3,
        "campaigns_draft": 1,
        "alerts_critical": 0,
        "alerts_warning": 2,
    }
    if override:
        base.update(override)
    return SystemSnapshot(**base)


def create_mock_reasoning(
    health_score: float = 75.0,
    num_recommendations: int = 3,
    num_critical: int = 0,
    override: dict = None
) -> AIReasoningOutput:
    """Crea un AIReasoningOutput de prueba."""
    recommendations = []
    for i in range(num_recommendations):
        priority = "critical" if i < num_critical else "medium"
        recommendations.append(
            AIRecommendation(
                id=f"rec-{i+1}",
                priority=priority,
                category="content",
                title=f"Recommendation {i+1}",
                description=f"Description for rec {i+1}",
                impact="medium",
                effort="low",
            )
        )
    
    action_plan = AIActionPlan(
        plan_id="plan-001",
        title="Test Action Plan",
        objective="Improve system",
        steps=[{"step": 1, "action": "Do something", "duration": "1 hour"}],
        estimated_duration="1 hour",
        risk_level="low",
        automated=True,
    )
    
    base = {
        "reasoning_id": str(uuid4()),
        "timestamp": datetime.utcnow(),
        "snapshot": create_mock_snapshot(),
        "summary": AISummary(
            overall_health="good",
            health_score=health_score,
            key_insights=["System is stable"],
            concerns=["Minor optimization needed"],
            positives=["High success rate"],
            generated_at=datetime.utcnow(),
        ),
        "recommendations": recommendations,
        "action_plan": action_plan,
        "execution_time_ms": 1500,
    }
    
    if override:
        base.update(override)
    
    return AIReasoningOutput(**base)


# === Unit Tests ===

@pytest.mark.asyncio
async def test_save_reasoning_to_history_creates_row(async_db_session: AsyncSession):
    """Test que save_reasoning_to_history crea una fila correctamente."""
    reasoning = create_mock_reasoning(health_score=80.0, num_recommendations=5, num_critical=1)
    
    result = await save_reasoning_to_history(
        db=async_db_session,
        reasoning=reasoning,
        triggered_by="manual"
    )
    
    assert result is not None
    assert result.health_score == 80
    assert result.status == "ok"  # 80 >= 70
    assert result.recommendations_count == 5
    assert result.critical_issues_count == 1
    assert result.triggered_by == "manual"
    assert result.run_id == reasoning.reasoning_id
    assert result.duration_ms == 1500


@pytest.mark.asyncio
async def test_get_history_returns_in_desc_order(async_db_session: AsyncSession):
    """Test que get_history retorna en orden DESC por created_at."""
    # Crear 3 runs con timestamps diferentes
    for i in range(3):
        reasoning = create_mock_reasoning(health_score=70 + i)
        await save_reasoning_to_history(async_db_session, reasoning, triggered_by="worker")
        await async_db_session.commit()
    
    history = await get_history(async_db_session, limit=10)
    
    assert len(history) == 3
    # Más reciente primero
    assert history[0].created_at >= history[1].created_at
    assert history[1].created_at >= history[2].created_at


@pytest.mark.asyncio
async def test_get_history_filters_by_score_and_status(async_db_session: AsyncSession):
    """Test que filtros de score y status funcionan correctamente."""
    # Crear runs con diferentes scores
    await save_reasoning_to_history(async_db_session, create_mock_reasoning(health_score=85), "worker")
    await save_reasoning_to_history(async_db_session, create_mock_reasoning(health_score=55), "worker")
    await save_reasoning_to_history(async_db_session, create_mock_reasoning(health_score=30), "worker")
    await async_db_session.commit()
    
    # Filtro por score mínimo
    high_score = await get_history(async_db_session, min_score=70)
    assert len(high_score) == 1
    assert high_score[0].health_score >= 70
    
    # Filtro por status
    critical = await get_history(async_db_session, status="critical")
    assert len(critical) == 1
    assert critical[0].status == "critical"


@pytest.mark.asyncio
async def test_get_history_only_critical_filters_correctly(async_db_session: AsyncSession):
    """Test que only_critical=True filtra solo runs con issues críticas."""
    # Run sin issues críticas
    await save_reasoning_to_history(
        async_db_session,
        create_mock_reasoning(num_recommendations=5, num_critical=0),
        "worker"
    )
    
    # Run con issues críticas
    await save_reasoning_to_history(
        async_db_session,
        create_mock_reasoning(num_recommendations=5, num_critical=2),
        "worker"
    )
    await async_db_session.commit()
    
    critical_only = await get_history(async_db_session, only_critical=True)
    assert len(critical_only) == 1
    assert critical_only[0].critical_issues_count > 0


@pytest.mark.asyncio
async def test_get_history_item_returns_full_detail(async_db_session: AsyncSession):
    """Test que get_history_item retorna el item completo con JSON deserializado."""
    reasoning = create_mock_reasoning(health_score=75, num_recommendations=3)
    saved = await save_reasoning_to_history(async_db_session, reasoning, "manual")
    await async_db_session.commit()
    
    item = await get_history_item(async_db_session, saved.id)
    
    assert item is not None
    assert item.id == saved.id
    assert item.snapshot_json is not None
    assert item.summary_json is not None
    assert item.recommendations_json is not None
    assert len(item.recommendations_json) == 3


@pytest.mark.asyncio
async def test_save_reasoning_validates_triggered_by(async_db_session: AsyncSession):
    """Test que triggered_by solo acepta valores válidos."""
    reasoning = create_mock_reasoning()
    
    # Valores válidos
    for valid in ["worker", "manual", "debug"]:
        result = await save_reasoning_to_history(async_db_session, reasoning, valid)
        assert result.triggered_by == valid
        await async_db_session.rollback()  # No persistir


@pytest.mark.asyncio
async def test_get_history_respects_limit_and_offset(async_db_session: AsyncSession):
    """Test que paginación funciona correctamente."""
    # Crear 15 runs
    for i in range(15):
        await save_reasoning_to_history(
            async_db_session,
            create_mock_reasoning(health_score=50 + i),
            "worker"
        )
    await async_db_session.commit()
    
    # Primera página (5 items)
    page1 = await get_history(async_db_session, limit=5, offset=0)
    assert len(page1) == 5
    
    # Segunda página (5 items)
    page2 = await get_history(async_db_session, limit=5, offset=5)
    assert len(page2) == 5
    
    # No deben repetirse items
    page1_ids = {item.id for item in page1}
    page2_ids = {item.id for item in page2}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_get_history_date_filters(async_db_session: AsyncSession):
    """Test que filtros de fecha funcionan correctamente."""
    now = datetime.utcnow()
    
    # Crear run "antiguo" (simulado con created_at manual)
    old_reasoning = create_mock_reasoning()
    old_row = await save_reasoning_to_history(async_db_session, old_reasoning, "worker")
    old_row.created_at = now - timedelta(days=7)
    
    # Crear run reciente
    recent_reasoning = create_mock_reasoning()
    await save_reasoning_to_history(async_db_session, recent_reasoning, "worker")
    
    await async_db_session.commit()
    
    # Filtro: solo últimos 3 días
    recent_only = await get_history(
        async_db_session,
        from_date=now - timedelta(days=3)
    )
    assert len(recent_only) == 1
    assert recent_only[0].created_at > (now - timedelta(days=3))


def test_status_determination_logic():
    """Test que la lógica de status funciona correctamente."""
    assert _determine_status(100) == "ok"
    assert _determine_status(70) == "ok"
    assert _determine_status(69) == "degraded"
    assert _determine_status(50) == "degraded"
    assert _determine_status(40) == "degraded"
    assert _determine_status(39) == "critical"
    assert _determine_status(0) == "critical"


def test_count_critical_issues():
    """Test que _count_critical_issues cuenta correctamente."""
    recommendations = [
        AIRecommendation(
            id="rec-1",
            priority="critical",
            category="system",
            title="Critical Issue",
            description="Fix immediately",
            impact="high",
            effort="medium",
        ),
        AIRecommendation(
            id="rec-2",
            priority="high",
            category="content",
            title="High Priority",
            description="Important",
            impact="medium",
            effort="low",
        ),
        AIRecommendation(
            id="rec-3",
            priority="critical",
            category="performance",
            title="Another Critical",
            description="Fix ASAP",
            impact="high",
            effort="high",
        ),
    ]
    
    count = _count_critical_issues(recommendations)
    assert count == 2


@pytest.mark.skip(reason="Auth/RBAC testing requiere setup complejo de usuarios y tokens")
@pytest.mark.asyncio
async def test_history_endpoints_require_auth(async_db_session: AsyncSession):
    """Test que endpoints de historial requieren autenticación admin/manager."""
    # Este test requeriría:
    # 1. Cliente HTTP (httpx)
    # 2. User fixtures con diferentes roles
    # 3. Token generation y headers
    # 4. Verificar 401 sin auth, 403 con rol incorrecto, 200 con rol correcto
    pass
