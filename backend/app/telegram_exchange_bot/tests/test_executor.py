"""
Tests for Sprint 7B - Executor Module
Test de ejecución de interacciones con seguridad.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.telegram_exchange_bot.executor import (
    InteractionExecutor,
    ExecutionResult,
    ExecutionStatus,
    YouTubeExecutor,
    InstagramExecutor
)
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccount,
    AccountStatus,
    AccountHealth
)
from app.telegram_exchange_bot.security import SecurityContext
from app.telegram_exchange_bot.models import InteractionType, Platform


@pytest.fixture
def mock_account():
    """Mock account para tests."""
    return NonOfficialAccount(
        account_id="test_acc_001",
        platform="youtube",
        username="test_support",
        status=AccountStatus.ACTIVE,
        health=AccountHealth.HEALTHY,
        total_interactions=10,
        successful_interactions=9,
        failed_interactions=1,
        interactions_today=5,
        interactions_this_hour=2
    )


@pytest.fixture
def mock_security_context(mock_account):
    """Mock security context."""
    return SecurityContext(
        vpn_active=True,
        proxy_url="http://proxy.test:8080",
        fingerprint_id="fp_test_123",
        account_id=mock_account.account_id
    )


@pytest.fixture
def mock_accounts_pool(mock_account):
    """Mock accounts pool."""
    pool = Mock()
    pool.get_account = AsyncMock(return_value=mock_account)
    pool.mark_used = AsyncMock()
    return pool


@pytest.fixture
def mock_security_layer(mock_security_context):
    """Mock security layer."""
    security = Mock()
    security.get_security_context = AsyncMock(return_value=mock_security_context)
    return security


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def executor(mock_accounts_pool, mock_security_layer, mock_db):
    """InteractionExecutor fixture."""
    return InteractionExecutor(
        accounts_pool=mock_accounts_pool,
        security_layer=mock_security_layer,
        db=mock_db
    )


# ============================================================================
# EXECUTOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_executor_initialization(executor):
    """Test: Executor se inicializa correctamente."""
    assert executor.accounts_pool is not None
    assert executor.security_layer is not None
    assert executor.db is not None
    assert len(executor.executors) >= 2  # YouTube + Instagram
    assert executor.stats["total_executions"] == 0


@pytest.mark.asyncio
async def test_execute_youtube_like_success(executor, mock_account):
    """Test: Ejecutar like en YouTube exitosamente."""
    result = await executor.execute_interaction(
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test123"
    )
    
    assert result is not None
    assert result.was_successful
    assert result.interaction_type == InteractionType.YOUTUBE_LIKE
    assert result.account_used == mock_account
    assert executor.stats["total_executions"] == 1
    assert executor.stats["successful_executions"] == 1


@pytest.mark.asyncio
async def test_execute_instagram_comment_success(executor, mock_account):
    """Test: Ejecutar comentario en Instagram exitosamente."""
    result = await executor.execute_interaction(
        interaction_type=InteractionType.INSTAGRAM_COMMENT,
        target_url="https://instagram.com/p/test123",
        comment_text="Great post! 🔥"
    )
    
    assert result.was_successful
    assert result.interaction_type == InteractionType.INSTAGRAM_COMMENT
    assert result.metadata.get("comment") == "Great post! 🔥"


@pytest.mark.asyncio
async def test_execute_without_account_fails(executor, mock_accounts_pool):
    """Test: Falla si no hay cuentas disponibles."""
    mock_accounts_pool.get_account = AsyncMock(return_value=None)
    
    result = await executor.execute_interaction(
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test"
    )
    
    assert not result.was_successful
    assert result.status == ExecutionStatus.FAILED
    assert "No accounts available" in result.error


@pytest.mark.asyncio
async def test_execute_comment_without_text_fails(executor):
    """Test: Falla si comentario sin texto."""
    result = await executor.execute_interaction(
        interaction_type=InteractionType.YOUTUBE_COMMENT,
        target_url="https://youtube.com/watch?v=test"
        # comment_text omitido
    )
    
    assert not result.was_successful
    assert "Comment text required" in result.error


@pytest.mark.asyncio
async def test_execute_batch_interactions(executor):
    """Test: Ejecutar batch de interacciones."""
    interactions = [
        {
            "interaction_type": InteractionType.YOUTUBE_LIKE,
            "target_url": "https://youtube.com/watch?v=1"
        },
        {
            "interaction_type": InteractionType.INSTAGRAM_LIKE,
            "target_url": "https://instagram.com/p/test"
        }
    ]
    
    results = await executor.execute_batch(interactions)
    
    assert len(results) == 2
    assert all(r.was_successful for r in results)


@pytest.mark.asyncio
async def test_executor_marks_account_as_used(executor, mock_accounts_pool):
    """Test: Marca cuenta como usada después de ejecutar."""
    await executor.execute_interaction(
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test"
    )
    
    # Verificar que se llamó mark_used
    mock_accounts_pool.mark_used.assert_called_once()


@pytest.mark.asyncio
async def test_executor_stats_tracking(executor):
    """Test: Stats se actualizan correctamente."""
    # Ejecutar 3 exitosas
    for i in range(3):
        await executor.execute_interaction(
            interaction_type=InteractionType.YOUTUBE_LIKE,
            target_url=f"https://youtube.com/watch?v=test{i}"
        )
    
    stats = executor.get_stats()
    assert stats["total_executions"] == 3
    assert stats["successful_executions"] == 3
    assert stats["success_rate"] == 1.0


# ============================================================================
# PLATFORM EXECUTOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_youtube_executor_like(mock_account, mock_security_context):
    """Test: YouTubeExecutor ejecuta like."""
    executor = YouTubeExecutor()
    
    result = await executor.execute_like(
        target_url="https://youtube.com/watch?v=test",
        account=mock_account,
        security_context=mock_security_context
    )
    
    assert result.was_successful
    assert result.interaction_type == InteractionType.YOUTUBE_LIKE


@pytest.mark.asyncio
async def test_instagram_executor_comment(mock_account, mock_security_context):
    """Test: InstagramExecutor ejecuta comentario."""
    executor = InstagramExecutor()
    
    result = await executor.execute_comment(
        target_url="https://instagram.com/p/test",
        comment_text="Nice!",
        account=mock_account,
        security_context=mock_security_context
    )
    
    assert result.was_successful
    assert result.interaction_type == InteractionType.INSTAGRAM_COMMENT
    assert result.metadata.get("comment") == "Nice!"


# ============================================================================
# EXECUTION RESULT TESTS
# ============================================================================

def test_execution_result_success(mock_account):
    """Test: ExecutionResult marca como exitoso."""
    result = ExecutionResult(
        status=ExecutionStatus.SUCCESS,
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test",
        account_used=mock_account,
        execution_time_seconds=2.5
    )
    
    assert result.was_successful
    assert result.status == ExecutionStatus.SUCCESS
    assert result.execution_time_seconds == 2.5


def test_execution_result_failed(mock_account):
    """Test: ExecutionResult marca como fallido."""
    result = ExecutionResult(
        status=ExecutionStatus.FAILED,
        interaction_type=InteractionType.YOUTUBE_LIKE,
        target_url="https://youtube.com/watch?v=test",
        account_used=mock_account,
        execution_time_seconds=0.5,
        error="Network timeout"
    )
    
    assert not result.was_successful
    assert result.error == "Network timeout"
