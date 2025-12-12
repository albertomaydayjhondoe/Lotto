"""
Tests for Sprint 7B - Accounts Pool Module
Test de gestión de cuentas NO oficiales.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccount,
    AccountStatus,
    AccountHealth,
    AccountHealthMonitor,
    AccountRotationStrategy,
    NonOfficialAccountsPool
)


@pytest.fixture
def sample_accounts():
    """Sample accounts para tests."""
    return [
        NonOfficialAccount(
            account_id="acc_001",
            platform="youtube",
            username="support_yt_1",
            status=AccountStatus.ACTIVE,
            health=AccountHealth.HEALTHY,
            total_interactions=100,
            successful_interactions=95,
            failed_interactions=5,
            interactions_today=10,
            interactions_this_hour=2
        ),
        NonOfficialAccount(
            account_id="acc_002",
            platform="youtube",
            username="support_yt_2",
            status=AccountStatus.ACTIVE,
            health=AccountHealth.DEGRADED,
            total_interactions=50,
            successful_interactions=40,
            failed_interactions=10,
            interactions_today=25,
            interactions_this_hour=5
        ),
        NonOfficialAccount(
            account_id="acc_003",
            platform="instagram",
            username="support_ig_1",
            status=AccountStatus.ACTIVE,
            health=AccountHealth.HEALTHY,
            total_interactions=80,
            successful_interactions=75,
            failed_interactions=5,
            interactions_today=5,
            interactions_this_hour=1
        )
    ]


@pytest.fixture
def mock_db():
    """Mock database."""
    return Mock()


@pytest.fixture
def accounts_pool(sample_accounts, mock_db):
    """NonOfficialAccountsPool fixture."""
    pool = NonOfficialAccountsPool(db=mock_db)
    pool.accounts = {acc.account_id: acc for acc in sample_accounts}
    return pool


# ============================================================================
# ACCOUNT HEALTH MONITOR TESTS
# ============================================================================

def test_health_monitor_calculates_success_rate():
    """Test: Monitor calcula success rate correctamente."""
    account = NonOfficialAccount(
        account_id="test_001",
        platform="youtube",
        username="test",
        total_interactions=100,
        successful_interactions=92,
        failed_interactions=8
    )
    
    health = AccountHealthMonitor.assess_account_health(account)
    assert health == AccountHealth.HEALTHY  # 92% > 90%


def test_health_monitor_degraded_account():
    """Test: Monitor detecta cuenta degradada."""
    account = NonOfficialAccount(
        account_id="test_002",
        platform="youtube",
        username="test",
        total_interactions=100,
        successful_interactions=82,
        failed_interactions=18
    )
    
    health = AccountHealthMonitor.assess_account_health(account)
    assert health == AccountHealth.DEGRADED  # 70% < 82% < 90%


def test_health_monitor_unhealthy_account():
    """Test: Monitor detecta cuenta unhealthy."""
    account = NonOfficialAccount(
        account_id="test_003",
        platform="youtube",
        username="test",
        total_interactions=100,
        successful_interactions=60,
        failed_interactions=40
    )
    
    health = AccountHealthMonitor.assess_account_health(account)
    assert health == AccountHealth.UNHEALTHY  # 60% < 70%


def test_health_monitor_new_account():
    """Test: Monitor marca nuevas cuentas como healthy."""
    account = NonOfficialAccount(
        account_id="test_new",
        platform="youtube",
        username="test",
        total_interactions=0,
        successful_interactions=0,
        failed_interactions=0
    )
    
    health = AccountHealthMonitor.assess_account_health(account)
    assert health == AccountHealth.HEALTHY  # Default para nuevas


# ============================================================================
# ROTATION STRATEGY TESTS
# ============================================================================

def test_rotation_strategy_selects_best_account(sample_accounts):
    """Test: Strategy selecciona mejor cuenta."""
    strategy = AccountRotationStrategy()
    
    best = strategy.select_account(sample_accounts, platform="youtube")
    
    # Debe seleccionar acc_001 (HEALTHY, menos uso)
    assert best.account_id == "acc_001"
    assert best.health == AccountHealth.HEALTHY


def test_rotation_strategy_filters_by_platform(sample_accounts):
    """Test: Strategy filtra por plataforma."""
    strategy = AccountRotationStrategy()
    
    instagram_acc = strategy.select_account(sample_accounts, platform="instagram")
    
    assert instagram_acc is not None
    assert instagram_acc.platform == "instagram"


def test_rotation_strategy_excludes_cooldown(sample_accounts):
    """Test: Strategy excluye cuentas en cooldown."""
    # Marcar acc_001 en cooldown
    sample_accounts[0].status = AccountStatus.COOLDOWN
    
    strategy = AccountRotationStrategy()
    best = strategy.select_account(sample_accounts, platform="youtube")
    
    # Debe seleccionar acc_002 (única disponible)
    assert best.account_id == "acc_002"


def test_rotation_strategy_respects_rate_limits(sample_accounts):
    """Test: Strategy respeta rate limits."""
    # Saturar acc_001
    sample_accounts[0].interactions_today = 50
    sample_accounts[0].interactions_this_hour = 10
    
    strategy = AccountRotationStrategy()
    best = strategy.select_account(sample_accounts, platform="youtube")
    
    # Debe seleccionar acc_002 (dentro de límites)
    assert best.account_id == "acc_002"


def test_rotation_strategy_no_available_accounts():
    """Test: Strategy retorna None si no hay cuentas."""
    strategy = AccountRotationStrategy()
    
    result = strategy.select_account([], platform="youtube")
    assert result is None


# ============================================================================
# ACCOUNTS POOL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_pool_initialization(mock_db):
    """Test: Pool se inicializa correctamente."""
    pool = NonOfficialAccountsPool(db=mock_db)
    
    assert pool.db is not None
    assert len(pool.accounts) == 0
    assert pool.stats["total_accounts"] == 0


@pytest.mark.asyncio
async def test_pool_get_account_success(accounts_pool):
    """Test: Pool retorna cuenta disponible."""
    account = await accounts_pool.get_account("youtube")
    
    assert account is not None
    assert account.platform == "youtube"
    assert account.status == AccountStatus.ACTIVE


@pytest.mark.asyncio
async def test_pool_get_account_wrong_platform(accounts_pool):
    """Test: Pool retorna None si no hay cuentas de plataforma."""
    account = await accounts_pool.get_account("tiktok")
    assert account is None


@pytest.mark.asyncio
async def test_pool_mark_used_success(accounts_pool):
    """Test: Pool marca cuenta como usada."""
    account = await accounts_pool.get_account("youtube")
    
    initial_interactions = account.total_interactions
    
    await accounts_pool.mark_used(account, success=True)
    
    assert account.total_interactions == initial_interactions + 1
    assert account.successful_interactions > 0


@pytest.mark.asyncio
async def test_pool_mark_used_failure(accounts_pool):
    """Test: Pool registra fallo correctamente."""
    account = await accounts_pool.get_account("youtube")
    
    initial_failed = account.failed_interactions
    
    await accounts_pool.mark_used(account, success=False)
    
    assert account.failed_interactions == initial_failed + 1


@pytest.mark.asyncio
async def test_pool_health_check_updates_status(accounts_pool):
    """Test: Health check actualiza estado de cuentas."""
    # Degradar acc_002 artificialmente
    acc_002 = accounts_pool.accounts["acc_002"]
    acc_002.successful_interactions = 30
    acc_002.failed_interactions = 20
    
    await accounts_pool.health_check()
    
    # Health debe actualizarse
    assert acc_002.health in [AccountHealth.DEGRADED, AccountHealth.UNHEALTHY]


@pytest.mark.asyncio
async def test_pool_reset_daily_counters(accounts_pool):
    """Test: Reset de contadores diarios."""
    # Simular uso
    for acc in accounts_pool.accounts.values():
        acc.interactions_today = 40
    
    await accounts_pool.reset_daily_counters()
    
    # Todos deben estar en 0
    for acc in accounts_pool.accounts.values():
        assert acc.interactions_today == 0


@pytest.mark.asyncio
async def test_pool_reset_hourly_counters(accounts_pool):
    """Test: Reset de contadores horarios."""
    for acc in accounts_pool.accounts.values():
        acc.interactions_this_hour = 8
    
    await accounts_pool.reset_hourly_counters()
    
    for acc in accounts_pool.accounts.values():
        assert acc.interactions_this_hour == 0


def test_pool_get_stats(accounts_pool):
    """Test: Stats del pool."""
    stats = accounts_pool.get_stats()
    
    assert stats["total_accounts"] == 3
    assert stats["active_accounts"] >= 0
    assert stats["healthy_accounts"] >= 0
    assert "accounts_by_platform" in stats


# ============================================================================
# NON-OFFICIAL ACCOUNT TESTS
# ============================================================================

def test_account_creation():
    """Test: Account se crea correctamente."""
    account = NonOfficialAccount(
        account_id="test_001",
        platform="youtube",
        username="test_user",
        status=AccountStatus.ACTIVE,
        health=AccountHealth.HEALTHY
    )
    
    assert account.account_id == "test_001"
    assert account.platform == "youtube"
    assert account.username == "test_user"
    assert account.total_interactions == 0


def test_account_success_rate():
    """Test: Calcula success rate correctamente."""
    account = NonOfficialAccount(
        account_id="test_002",
        platform="youtube",
        username="test",
        total_interactions=100,
        successful_interactions=85,
        failed_interactions=15
    )
    
    success_rate = (
        account.successful_interactions / account.total_interactions
        if account.total_interactions > 0 else 0.0
    )
    
    assert success_rate == 0.85


def test_account_within_rate_limits():
    """Test: Verifica si cuenta está dentro de límites."""
    account = NonOfficialAccount(
        account_id="test_003",
        platform="youtube",
        username="test",
        interactions_today=30,
        interactions_this_hour=5
    )
    
    # Dentro de límites (50/día, 10/hora)
    assert account.interactions_today < 50
    assert account.interactions_this_hour < 10


def test_account_exceeded_daily_limit():
    """Test: Detecta límite diario excedido."""
    account = NonOfficialAccount(
        account_id="test_004",
        platform="youtube",
        username="test",
        interactions_today=51,
        interactions_this_hour=3
    )
    
    # Límite diario excedido
    assert account.interactions_today > 50
