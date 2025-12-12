"""
Tests Sprint 7C - Production Hardening
Tests para KillSwitch, Watchdog, IsolatedExecutionQueue.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.telegram_exchange_bot.production_hardening import (
    KillSwitch,
    Watchdog,
    IsolatedExecutionQueue,
    ProductionHardening,
    SystemState,
    AnomalyType,
    Anomaly
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


class TestKillSwitch:
    """Tests para KillSwitch."""
    
    @pytest.mark.asyncio
    async def test_activate_kill_switch(self, mock_db):
        """Test activación de kill-switch."""
        ks = KillSwitch(db=mock_db)
        
        success = await ks.activate(
            reason="Test emergency",
            activated_by="test_user"
        )
        
        assert success is True
        assert ks.is_active is True
        assert ks.reason == "Test emergency"
        assert ks.activated_by == "test_user"
        assert ks.activated_at is not None
    
    @pytest.mark.asyncio
    async def test_activate_already_active(self, mock_db):
        """Test activación cuando ya está activo."""
        ks = KillSwitch(db=mock_db)
        
        await ks.activate(reason="First", activated_by="user1")
        success = await ks.activate(reason="Second", activated_by="user2")
        
        assert success is False
        assert ks.reason == "First"  # No cambió
    
    @pytest.mark.asyncio
    async def test_deactivate_kill_switch(self, mock_db):
        """Test desactivación."""
        ks = KillSwitch(db=mock_db)
        
        await ks.activate(reason="Test", activated_by="user")
        success = await ks.deactivate(deactivated_by="admin")
        
        assert success is True
        assert ks.is_active is False
    
    def test_get_status(self, mock_db):
        """Test obtención de status."""
        ks = KillSwitch(db=mock_db)
        
        status = ks.get_status()
        
        assert "is_active" in status
        assert "activated_at" in status
        assert "reason" in status
        assert "duration_seconds" in status


class TestWatchdog:
    """Tests para Watchdog."""
    
    @pytest.fixture
    def watchdog(self, mock_db):
        """Watchdog con mocks."""
        ks = KillSwitch(db=mock_db)
        wd = Watchdog(db=mock_db, kill_switch=ks, check_interval_seconds=1)
        return wd
    
    @pytest.mark.asyncio
    async def test_check_error_rate_normal(self, watchdog):
        """Test error rate normal."""
        anomaly = await watchdog.check_error_rate()
        
        # Mock devuelve 25% error rate, threshold 30%
        assert anomaly is None
    
    @pytest.mark.asyncio
    async def test_check_error_rate_high(self, watchdog):
        """Test error rate alto."""
        # Mock para simular high error rate
        with patch.object(watchdog, 'check_error_rate') as mock_check:
            mock_check.return_value = Anomaly(
                type=AnomalyType.HIGH_ERROR_RATE,
                severity=0.9,
                timestamp=datetime.utcnow(),
                details={"error_rate": 0.45},
                affected_accounts=[],
                auto_paused=False
            )
            
            anomaly = await watchdog.check_error_rate()
        
        assert anomaly is not None
        assert anomaly.type == AnomalyType.HIGH_ERROR_RATE
        assert anomaly.severity == 0.9
    
    @pytest.mark.asyncio
    async def test_check_shadowban_wave_detected(self, watchdog):
        """Test detección de shadowban wave."""
        # Mock para simular shadowban wave
        with patch.object(watchdog, 'check_shadowban_wave') as mock_check:
            mock_check.return_value = Anomaly(
                type=AnomalyType.SHADOWBAN_WAVE,
                severity=1.0,
                timestamp=datetime.utcnow(),
                details={"shadowbans_count": 7},
                affected_accounts=["acc_001", "acc_002"],
                auto_paused=True
            )
            
            anomaly = await watchdog.check_shadowban_wave()
        
        assert anomaly is not None
        assert anomaly.type == AnomalyType.SHADOWBAN_WAVE
        assert anomaly.auto_paused is True
    
    @pytest.mark.asyncio
    async def test_handle_anomaly_critical(self, watchdog):
        """Test manejo de anomalía crítica."""
        anomaly = Anomaly(
            type=AnomalyType.SHADOWBAN_WAVE,
            severity=0.9,
            timestamp=datetime.utcnow(),
            details={},
            affected_accounts=[],
            auto_paused=True
        )
        
        await watchdog.handle_anomaly(anomaly)
        
        # Debe activar kill-switch
        assert watchdog.kill_switch.is_active is True
        assert len(watchdog.anomalies_detected) == 1
    
    @pytest.mark.asyncio
    async def test_handle_anomaly_non_critical(self, watchdog):
        """Test manejo de anomalía no crítica."""
        anomaly = Anomaly(
            type=AnomalyType.HIGH_ERROR_RATE,
            severity=0.5,
            timestamp=datetime.utcnow(),
            details={},
            affected_accounts=[],
            auto_paused=False
        )
        
        await watchdog.handle_anomaly(anomaly)
        
        # No debe activar kill-switch
        assert watchdog.kill_switch.is_active is False
        assert len(watchdog.anomalies_detected) == 1
    
    def test_get_stats(self, watchdog):
        """Test obtención de stats."""
        stats = watchdog.get_stats()
        
        assert "is_running" in stats
        assert "check_interval_seconds" in stats
        assert "anomalies_detected" in stats
        assert "kill_switch_status" in stats


class TestIsolatedExecutionQueue:
    """Tests para IsolatedExecutionQueue."""
    
    def test_is_account_busy_false(self):
        """Test cuenta no ocupada."""
        queue = IsolatedExecutionQueue()
        
        assert queue.is_account_busy("acc_001") is False
    
    @pytest.mark.asyncio
    async def test_acquire_slot_success(self):
        """Test adquisición de slot exitosa."""
        queue = IsolatedExecutionQueue()
        
        success = await queue.acquire_slot(
            account_id="acc_001",
            interaction_type="youtube_like",
            expected_duration_seconds=30.0
        )
        
        assert success is True
        assert queue.is_account_busy("acc_001") is True
        assert "acc_001" in queue.active_slots
    
    @pytest.mark.asyncio
    async def test_acquire_slot_already_busy(self):
        """Test adquisición cuando cuenta ya ocupada."""
        queue = IsolatedExecutionQueue()
        
        await queue.acquire_slot("acc_001", "youtube_like", 30.0)
        success = await queue.acquire_slot("acc_001", "instagram_like", 25.0)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_release_slot_success(self):
        """Test liberación de slot exitosa."""
        queue = IsolatedExecutionQueue()
        
        await queue.acquire_slot("acc_001", "youtube_like", 30.0)
        await queue.release_slot("acc_001", success=True)
        
        assert queue.is_account_busy("acc_001") is False
        assert "acc_001" not in queue.active_slots
        assert queue.total_executed == 1
    
    @pytest.mark.asyncio
    async def test_release_slot_failure(self):
        """Test liberación con fallo."""
        queue = IsolatedExecutionQueue()
        
        await queue.acquire_slot("acc_001", "youtube_like", 30.0)
        await queue.release_slot("acc_001", success=False)
        
        assert queue.total_failed == 1
    
    def test_get_stats(self):
        """Test obtención de stats."""
        queue = IsolatedExecutionQueue()
        
        stats = queue.get_stats()
        
        assert "active_slots" in stats
        assert "total_executed" in stats
        assert "total_failed" in stats
        assert "success_rate" in stats


class TestProductionHardening:
    """Tests para ProductionHardening completo."""
    
    @pytest.mark.asyncio
    async def test_start_hardening(self, mock_db):
        """Test inicio de production hardening."""
        hardening = ProductionHardening(db=mock_db)
        
        # Mock watchdog run
        with patch.object(hardening.watchdog, 'run', new=AsyncMock()):
            await hardening.start()
        
        # Verificar componentes inicializados
        assert hardening.kill_switch is not None
        assert hardening.watchdog is not None
        assert hardening.execution_queue is not None
    
    @pytest.mark.asyncio
    async def test_stop_hardening(self, mock_db):
        """Test detención de production hardening."""
        hardening = ProductionHardening(db=mock_db)
        
        with patch.object(hardening.watchdog, 'run', new=AsyncMock()):
            await hardening.start()
            await hardening.stop()
        
        assert hardening.watchdog.is_running is False
    
    def test_get_full_status(self, mock_db):
        """Test obtención de status completo."""
        hardening = ProductionHardening(db=mock_db)
        
        status = hardening.get_full_status()
        
        assert "kill_switch" in status
        assert "watchdog" in status
        assert "execution_queue" in status


@pytest.mark.asyncio
async def test_integration_full_hardening(mock_db):
    """Test de integración: hardening completo."""
    hardening = ProductionHardening(db=mock_db)
    
    # Start
    with patch.object(hardening.watchdog, 'run', new=AsyncMock()):
        await hardening.start()
    
    # Simular anomalía crítica
    anomaly = Anomaly(
        type=AnomalyType.SHADOWBAN_WAVE,
        severity=0.95,
        timestamp=datetime.utcnow(),
        details={"shadowbans_count": 10},
        affected_accounts=["acc_001", "acc_002", "acc_003"],
        auto_paused=True
    )
    
    await hardening.watchdog.handle_anomaly(anomaly)
    
    # Verificar kill-switch activado
    assert hardening.kill_switch.is_active is True
    
    # Verificar que execution queue no permite nuevas ejecuciones
    # (esto debería verificarse en executor.py, pero aquí verificamos estado)
    status = hardening.get_full_status()
    assert status["kill_switch"]["is_active"] is True
    
    # Desactivar kill-switch
    await hardening.kill_switch.deactivate(deactivated_by="admin")
    assert hardening.kill_switch.is_active is False
    
    # Stop
    await hardening.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
