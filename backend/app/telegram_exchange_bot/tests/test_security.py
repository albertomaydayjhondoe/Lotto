"""
Tests for Sprint 7B - Security Module
Test de validación de seguridad VPN+Proxy+Fingerprint.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.telegram_exchange_bot.security import (
    TelegramBotSecurityLayer,
    SecurityContext,
    SecurityValidator,
    SecurityException,
    AntiShadowbanProtection
)
from app.telegram_exchange_bot.accounts_pool import (
    NonOfficialAccount,
    AccountStatus,
    AccountHealth
)


@pytest.fixture
def mock_account():
    """Mock account."""
    return NonOfficialAccount(
        account_id="test_acc_001",
        platform="youtube",
        username="test_support",
        status=AccountStatus.ACTIVE,
        health=AccountHealth.HEALTHY
    )


@pytest.fixture
def mock_isolator():
    """Mock TelegramBotIsolator."""
    isolator = Mock()
    isolator.is_vpn_active = Mock(return_value=True)
    isolator.get_current_vpn_location = Mock(return_value="US-East")
    return isolator


@pytest.fixture
def mock_proxy_router():
    """Mock ProxyRouter."""
    router = Mock()
    router.get_proxy_for_account = AsyncMock(return_value="http://proxy.test:8080")
    router.rotate_proxy = AsyncMock(return_value="http://proxy2.test:8080")
    return router


@pytest.fixture
def mock_fingerprint_manager():
    """Mock FingerprintManager."""
    manager = Mock()
    manager.get_fingerprint = Mock(return_value="fp_test_123")
    return manager


@pytest.fixture
def security_layer(mock_isolator, mock_proxy_router, mock_fingerprint_manager):
    """TelegramBotSecurityLayer fixture."""
    return TelegramBotSecurityLayer(
        isolator=mock_isolator,
        proxy_router=mock_proxy_router,
        fingerprint_manager=mock_fingerprint_manager
    )


# ============================================================================
# SECURITY LAYER TESTS
# ============================================================================

def test_security_layer_initialization(security_layer):
    """Test: SecurityLayer se inicializa correctamente."""
    assert security_layer.isolator is not None
    assert security_layer.proxy_router is not None
    assert security_layer.fingerprint_manager is not None
    assert security_layer.stats["operations_secured"] == 0


@pytest.mark.asyncio
async def test_get_security_context_success(security_layer, mock_account):
    """Test: Obtiene contexto de seguridad exitosamente."""
    context = await security_layer.get_security_context(
        account=mock_account,
        operation="like"
    )
    
    assert context is not None
    assert context.vpn_active is True
    assert context.proxy_url == "http://proxy.test:8080"
    assert context.fingerprint_id == "fp_test_123"
    assert context.account_id == mock_account.account_id


@pytest.mark.asyncio
async def test_security_context_without_vpn_fails(security_layer, mock_account, mock_isolator):
    """Test: Falla si VPN no está activa."""
    mock_isolator.is_vpn_active = Mock(return_value=False)
    
    with pytest.raises(SecurityException) as exc_info:
        await security_layer.get_security_context(mock_account, "like")
    
    assert "VPN must be active" in str(exc_info.value)


@pytest.mark.asyncio
async def test_security_context_without_proxy_fails(security_layer, mock_account, mock_proxy_router):
    """Test: Falla si no hay proxy asignado."""
    mock_proxy_router.get_proxy_for_account = AsyncMock(return_value=None)
    
    with pytest.raises(SecurityException) as exc_info:
        await security_layer.get_security_context(mock_account, "like")
    
    assert "Proxy must be assigned" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_before_execution_success(security_layer, mock_account):
    """Test: Validación antes de ejecución pasa."""
    context = await security_layer.get_security_context(mock_account, "like")
    
    # No debe lanzar excepción
    await security_layer.validate_before_execution(context, "like")
    
    assert security_layer.stats["operations_secured"] > 0


@pytest.mark.asyncio
async def test_circuit_breaker_activates_after_violations(security_layer, mock_account, mock_isolator):
    """Test: Circuit breaker se activa después de violaciones."""
    # Simular 10 violaciones de seguridad
    mock_isolator.is_vpn_active = Mock(return_value=False)
    
    for i in range(10):
        try:
            await security_layer.get_security_context(mock_account, "like")
        except SecurityException:
            pass
    
    # Circuit breaker debe estar activo
    assert security_layer.circuit_breaker_active is True


@pytest.mark.asyncio
async def test_rotate_proxy_for_account(security_layer, mock_account):
    """Test: Rota proxy para cuenta."""
    new_proxy = await security_layer.rotate_proxy(mock_account)
    
    assert new_proxy == "http://proxy2.test:8080"
    assert security_layer.stats["proxy_rotations"] > 0


@pytest.mark.asyncio
async def test_report_security_incident(security_layer, mock_account):
    """Test: Reporta incidente de seguridad."""
    await security_layer.report_security_incident(
        account=mock_account,
        incident_type="shadowban_detected",
        details={"reason": "Too many requests"}
    )
    
    # Verificar que se incrementó contador
    assert security_layer.stats["security_violations"] > 0


def test_security_layer_stats(security_layer):
    """Test: Stats se retornan correctamente."""
    stats = security_layer.get_stats()
    
    assert "operations_secured" in stats
    assert "security_violations" in stats
    assert "vpn_failures" in stats
    assert "proxy_rotations" in stats
    assert "circuit_breaker_active" in stats


# ============================================================================
# SECURITY VALIDATOR TESTS
# ============================================================================

def test_validator_vpn_required():
    """Test: Validador requiere VPN."""
    context = SecurityContext(
        vpn_active=False,
        proxy_url="http://proxy.test:8080",
        fingerprint_id="fp_123",
        account_id="acc_001"
    )
    
    with pytest.raises(SecurityException) as exc_info:
        SecurityValidator.validate_execution_context(
            context=context,
            operation="like",
            require_vpn=True
        )
    
    assert "VPN not active" in str(exc_info.value)


def test_validator_proxy_required():
    """Test: Validador requiere proxy."""
    context = SecurityContext(
        vpn_active=True,
        proxy_url=None,
        fingerprint_id="fp_123",
        account_id="acc_001"
    )
    
    with pytest.raises(SecurityException) as exc_info:
        SecurityValidator.validate_execution_context(
            context=context,
            operation="like",
            require_proxy=True
        )
    
    assert "Proxy not assigned" in str(exc_info.value)


def test_validator_fingerprint_optional():
    """Test: Fingerprint es opcional."""
    context = SecurityContext(
        vpn_active=True,
        proxy_url="http://proxy.test:8080",
        fingerprint_id=None,
        account_id="acc_001"
    )
    
    # No debe lanzar excepción
    SecurityValidator.validate_execution_context(
        context=context,
        operation="like",
        require_fingerprint=False
    )


# ============================================================================
# ANTI-SHADOWBAN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_anti_shadowban_human_delay():
    """Test: Delay humano se aplica."""
    import time
    start = time.time()
    
    await AntiShadowbanProtection.apply_human_delay(
        operation="like",
        min_seconds=0.1,
        max_seconds=0.2
    )
    
    elapsed = time.time() - start
    assert elapsed >= 0.1
    assert elapsed <= 0.3  # Margen


def test_anti_shadowban_cooldown_recommendations():
    """Test: Recomendaciones de cooldown."""
    cooldown = AntiShadowbanProtection.get_recommended_cooldown("like")
    assert cooldown >= 30  # Al menos 30 segundos
    
    cooldown_comment = AntiShadowbanProtection.get_recommended_cooldown("comment")
    assert cooldown_comment > cooldown  # Comentarios requieren más cooldown


# ============================================================================
# SECURITY CONTEXT TESTS
# ============================================================================

def test_security_context_creation():
    """Test: SecurityContext se crea correctamente."""
    context = SecurityContext(
        vpn_active=True,
        proxy_url="http://proxy.test:8080",
        fingerprint_id="fp_123",
        account_id="acc_001"
    )
    
    assert context.vpn_active is True
    assert context.proxy_url == "http://proxy.test:8080"
    assert context.fingerprint_id == "fp_123"
    assert context.account_id == "acc_001"


def test_security_context_is_valid():
    """Test: Validez de contexto de seguridad."""
    valid_context = SecurityContext(
        vpn_active=True,
        proxy_url="http://proxy.test:8080",
        fingerprint_id="fp_123",
        account_id="acc_001"
    )
    
    invalid_context = SecurityContext(
        vpn_active=False,
        proxy_url=None,
        fingerprint_id=None,
        account_id="acc_001"
    )
    
    # Valid context debe pasar validación mínima
    assert valid_context.vpn_active is True
    assert valid_context.proxy_url is not None
    
    # Invalid context no cumple requisitos
    assert invalid_context.vpn_active is False
    assert invalid_context.proxy_url is None
