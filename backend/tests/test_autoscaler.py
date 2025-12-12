"""
Tests Sprint 7C - Auto-Scaler
Tests para AccountAutoScaler.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.telegram_exchange_bot.autoscaler import (
    AccountAutoScaler,
    ScalingTrigger,
    ScalingEvent
)
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccountsPool,
    AccountHealthMonitor,
    Account
)
from app.telegram_exchange_bot.security import TelegramBotSecurityLayer


@pytest.fixture
def mock_pool():
    """Mock de NonOfficialAccountsPool."""
    pool = Mock(spec=NonOfficialAccountsPool)
    
    # Cuentas mock
    pool.accounts = {
        f"acc_{i:03d}": Mock(
            account_id=f"acc_{i:03d}",
            is_active=True,
            is_cooling_down=False
        )
        for i in range(5)
    }
    
    return pool


@pytest.fixture
def mock_health_monitor():
    """Mock de AccountHealthMonitor."""
    monitor = Mock(spec=AccountHealthMonitor)
    
    # Health scores mock (0.8 para la mayoría, 0.2 para acc_004)
    def get_health_score(account_id):
        if account_id == "acc_004":
            return 0.2  # Unhealthy
        return 0.8  # Healthy
    
    monitor.get_health_score = Mock(side_effect=get_health_score)
    
    return monitor


@pytest.fixture
def mock_security_layer():
    """Mock de TelegramBotSecurityLayer."""
    layer = Mock(spec=TelegramBotSecurityLayer)
    
    async def prepare_security_context(*args, **kwargs):
        return Mock(
            account_id=kwargs.get("account_id"),
            vpn_active=True,
            proxy=Mock(host="proxy.test", port=8080),
            fingerprint="mock_fingerprint",
            rate_limit_respected=True
        )
    
    layer.prepare_security_context = AsyncMock(side_effect=prepare_security_context)
    
    return layer


@pytest.fixture
def autoscaler(mock_pool, mock_health_monitor, mock_security_layer):
    """AccountAutoScaler con mocks."""
    db = Mock()
    
    scaler = AccountAutoScaler(
        pool=mock_pool,
        health_monitor=mock_health_monitor,
        security_layer=mock_security_layer,
        db=db
    )
    
    return scaler


class TestAccountAutoScaler:
    """Tests para AccountAutoScaler."""
    
    def test_calculate_pool_load_normal(self, autoscaler, mock_pool):
        """Test cálculo de load normal."""
        load = autoscaler.calculate_pool_load()
        
        # 5 active accounts / 5 healthy accounts = 1.0
        assert load == 1.0
    
    def test_get_unhealthy_accounts(self, autoscaler):
        """Test detección de cuentas unhealthy."""
        unhealthy = autoscaler.get_unhealthy_accounts()
        
        # acc_004 tiene health=0.2 < 0.3
        assert "acc_004" in unhealthy
        assert len(unhealthy) == 1
    
    @pytest.mark.asyncio
    async def test_activate_new_accounts_normal(self, autoscaler):
        """Test activación de nuevas cuentas."""
        with patch('asyncio.sleep', new=AsyncMock()):
            activated, new_ids = await autoscaler.activate_new_accounts(
                count=2,
                trigger=ScalingTrigger.HIGH_LOAD,
                reason="Test high load"
            )
        
        assert activated == 2
        assert len(new_ids) == 2
        assert autoscaler.new_accounts_today == 2
        assert len(autoscaler.scaling_events) == 1
    
    @pytest.mark.asyncio
    async def test_activate_new_accounts_daily_limit(self, autoscaler):
        """Test rate limiting diario."""
        autoscaler.new_accounts_today = 10  # Ya en el límite
        
        activated, new_ids = await autoscaler.activate_new_accounts(
            count=5,
            trigger=ScalingTrigger.HIGH_LOAD,
            reason="Test limit"
        )
        
        assert activated == 0
        assert len(new_ids) == 0
    
    @pytest.mark.asyncio
    async def test_apply_cooldown(self, autoscaler, mock_pool):
        """Test aplicación de cooldown."""
        account_ids = ["acc_001", "acc_002"]
        
        cooled = await autoscaler.apply_cooldown(account_ids)
        
        assert cooled == 2
        assert mock_pool.accounts["acc_001"].is_cooling_down is True
        assert mock_pool.accounts["acc_001"].is_active is False
    
    @pytest.mark.asyncio
    async def test_check_and_scale_high_load(self, autoscaler, mock_pool):
        """Test scaling por high load."""
        # Forzar high load
        autoscaler.high_load_threshold = 0.5  # Threshold bajo
        
        with patch('asyncio.sleep', new=AsyncMock()):
            event = await autoscaler.check_and_scale()
        
        # Debe escalar
        assert event is not None
        assert event.trigger == ScalingTrigger.HIGH_LOAD
        assert event.success is True
    
    @pytest.mark.asyncio
    async def test_check_and_scale_unhealthy_accounts(self, autoscaler):
        """Test cooldown por unhealthy accounts."""
        event = await autoscaler.check_and_scale()
        
        # acc_004 debe estar en cooldown
        # No retorna event porque no se escaló, solo cooldown
        # Pero acc_004 debe estar enfriada
        # (verificar en mock_pool si se llamó)
    
    def test_get_stats(self, autoscaler):
        """Test obtención de stats."""
        stats = autoscaler.get_stats()
        
        assert "is_running" in stats
        assert "current_load" in stats
        assert "new_accounts_today" in stats
        assert "max_new_accounts_per_day" in stats
        assert stats["max_new_accounts_per_day"] == 10


@pytest.mark.asyncio
async def test_autoscaler_integration(mock_pool, mock_health_monitor, mock_security_layer):
    """Test de integración: autoscaler completo."""
    db = Mock()
    
    autoscaler = AccountAutoScaler(
        pool=mock_pool,
        health_monitor=mock_health_monitor,
        security_layer=mock_security_layer,
        db=db
    )
    
    # Simular high load
    autoscaler.high_load_threshold = 0.5
    
    with patch('asyncio.sleep', new=AsyncMock()):
        # Primera iteración: detectar y escalar
        event1 = await autoscaler.check_and_scale()
        
        assert event1 is not None
        assert autoscaler.new_accounts_today > 0
        
        # Segunda iteración: daily reset
        autoscaler.last_daily_reset = datetime.utcnow().date() - timedelta(days=1)
        event2 = await autoscaler.check_and_scale()
        
        # Debe resetear contador
        # (depende de la lógica interna)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
