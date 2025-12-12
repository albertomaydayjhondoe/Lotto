"""
🧪 TESTS DE AISLAMIENTO DE IDENTIDAD

Tests comprehensivos para verificar que la política de aislamiento
se cumple correctamente.

VALIDA:
- Proxies únicos por satélite
- VPN exclusiva para TelegramBot
- No hay IPs compartidas
- Fingerprints únicos
- Isolation coverage

Autor: STAKAZO Security Team
Fecha: Diciembre 2025
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.core.proxy_router import (
    ProxyRouter, ComponentType, ProxyConfig, ProxyType
)
from app.core.fingerprint_manager import (
    FingerprintManager, DeviceType, FingerprintProfile
)
from app.satellites.models import SatelliteAccount, PlatformType
from app.satellites.config import SatelliteConfig
from app.satellites.account_management.account_manager import AccountManager
from app.exchange.telegram_bot_isolator import TelegramBotProxyIsolator


# ============================================================================
# TESTS: ProxyRouter
# ============================================================================

class TestProxyRouter:
    """Tests para ProxyRouter"""
    
    def test_satellite_gets_unique_proxy(self):
        """Cada satélite debe recibir un proxy único"""
        router = ProxyRouter()
        
        # Asignar proxies a 3 satélites
        proxy1 = router.assign_proxy("sat1", ComponentType.SATELLITE_ACCOUNT)
        proxy2 = router.assign_proxy("sat2", ComponentType.SATELLITE_ACCOUNT)
        proxy3 = router.assign_proxy("sat3", ComponentType.SATELLITE_ACCOUNT)
        
        # Verificar que todos tienen proxy
        assert proxy1 is not None
        assert proxy2 is not None
        assert proxy3 is not None
        
        # Verificar que son únicos
        assert proxy1.proxy_id != proxy2.proxy_id
        assert proxy2.proxy_id != proxy3.proxy_id
        assert proxy1.proxy_id != proxy3.proxy_id
        
        # Verificar que están asignados
        assert proxy1.assigned_to == "sat1"
        assert proxy2.assigned_to == "sat2"
        assert proxy3.assigned_to == "sat3"
    
    def test_telegram_bot_gets_vpn(self):
        """TelegramBot debe recibir VPN exclusiva"""
        router = ProxyRouter()
        
        proxy = router.assign_proxy("telegram_bot", ComponentType.TELEGRAM_BOT)
        
        assert proxy is not None
        assert proxy.proxy_type == ProxyType.VPN
        assert "telegram" in proxy.proxy_id.lower()
    
    def test_telegram_bot_never_shares_satellite_ip(self):
        """TelegramBot NO debe compartir IP con satélites"""
        router = ProxyRouter()
        
        # Asignar proxy a satélite
        sat_proxy = router.assign_proxy("sat1", ComponentType.SATELLITE_ACCOUNT)
        
        # Asignar VPN a TelegramBot
        bot_proxy = router.assign_proxy("telegram_bot", ComponentType.TELEGRAM_BOT)
        
        # Verificar que NO comparten IP
        assert sat_proxy.host != bot_proxy.host
    
    def test_official_api_no_proxy(self):
        """APIs oficiales NO deben usar proxy"""
        router = ProxyRouter()
        
        proxy = router.assign_proxy("meta_ads", ComponentType.OFFICIAL_API)
        
        # Debe retornar None (usa backend IP)
        assert proxy is None
    
    def test_validate_request_blocks_violations(self):
        """validate_request debe bloquear violaciones de política"""
        router = ProxyRouter()
        
        # Caso 1: Satélite SIN proxy (BLOQUEADO)
        is_valid = router.validate_request("sat_without_proxy", ComponentType.SATELLITE_ACCOUNT)
        assert is_valid is False
        assert router.blocked_attempts > 0
        
        # Caso 2: API oficial CON proxy (BLOQUEADO)
        router.assign_proxy("api_with_proxy", ComponentType.SATELLITE_ACCOUNT)  # Asignar por error
        is_valid = router.validate_request("api_with_proxy", ComponentType.OFFICIAL_API)
        assert is_valid is False
        
        # Caso 3: Satélite CON proxy (PERMITIDO)
        router.assign_proxy("sat_valid", ComponentType.SATELLITE_ACCOUNT)
        is_valid = router.validate_request("sat_valid", ComponentType.SATELLITE_ACCOUNT)
        assert is_valid is True
    
    def test_scraper_proxy_rotation(self):
        """Scrapers deben rotar entre pool de proxies"""
        router = ProxyRouter()
        
        # Asignar a múltiples scrapers
        proxy1 = router.assign_proxy("scraper1", ComponentType.SCRAPER)
        proxy2 = router.assign_proxy("scraper2", ComponentType.SCRAPER)
        proxy3 = router.assign_proxy("scraper3", ComponentType.SCRAPER)
        
        # Todos deben tener proxy
        assert proxy1 is not None
        assert proxy2 is not None
        assert proxy3 is not None
        
        # Pueden compartir proxies del pool (rotación)
        # Pero NO deben compartir con satélites o TelegramBot
        sat_proxy = router.assign_proxy("sat1", ComponentType.SATELLITE_ACCOUNT)
        bot_proxy = router.assign_proxy("bot1", ComponentType.TELEGRAM_BOT)
        
        scraper_ips = {proxy1.host, proxy2.host, proxy3.host}
        assert sat_proxy.host not in scraper_ips
        assert bot_proxy.host not in scraper_ips
    
    def test_isolation_policy_validation(self):
        """validate_isolation_policy debe detectar violaciones"""
        router = ProxyRouter()
        
        # Setup correcto
        router.assign_proxy("sat1", ComponentType.SATELLITE_ACCOUNT)
        router.assign_proxy("sat2", ComponentType.SATELLITE_ACCOUNT)
        router.assign_proxy("telegram_bot", ComponentType.TELEGRAM_BOT)
        
        validations = router.validate_isolation_policy()
        
        # Todas las validaciones deben pasar
        assert validations["no_shared_ips_satellites"] is True
        assert validations["telegram_bot_isolated"] is True
        assert validations["scrapers_separate_pool"] is True
    
    def test_proxy_url_generation(self):
        """get_proxy_url debe generar URL correcta"""
        router = ProxyRouter()
        
        router.assign_proxy("sat1", ComponentType.SATELLITE_ACCOUNT)
        url = router.get_proxy_url("sat1")
        
        assert url is not None
        assert url.startswith("http://") or url.startswith("https://")
        assert "@" in url  # Debe tener credenciales


# ============================================================================
# TESTS: FingerprintManager
# ============================================================================

class TestFingerprintManager:
    """Tests para FingerprintManager"""
    
    def test_generate_unique_fingerprints(self):
        """Cada componente debe recibir fingerprint único"""
        manager = FingerprintManager()
        
        fp1 = manager.generate_fingerprint("sat1", DeviceType.ANDROID_MOBILE)
        fp2 = manager.generate_fingerprint("sat2", DeviceType.ANDROID_MOBILE)
        fp3 = manager.generate_fingerprint("sat3", DeviceType.IOS_MOBILE)
        
        # Verificar que son únicos
        assert fp1.profile_id != fp2.profile_id != fp3.profile_id
        assert fp1.canvas_fingerprint != fp2.canvas_fingerprint
        assert fp1.user_agent != fp2.user_agent
    
    def test_telegram_bot_gets_generic_pc(self):
        """TelegramBot debe tener fingerprint Generic PC"""
        manager = FingerprintManager()
        
        fp = manager.generate_fingerprint("telegram_bot", DeviceType.GENERIC_PC, "US")
        
        assert fp.device_type == DeviceType.GENERIC_PC
        assert "Windows" in fp.user_agent or "Win32" in fp.platform
        assert fp.pixel_ratio == 1.0  # PC típico
    
    def test_satellite_gets_mobile_fingerprint(self):
        """Satélites deben tener fingerprints móviles"""
        manager = FingerprintManager()
        
        fp_android = manager.generate_fingerprint("sat1", DeviceType.ANDROID_MOBILE)
        fp_ios = manager.generate_fingerprint("sat2", DeviceType.IOS_MOBILE)
        
        # Android
        assert fp_android.device_type == DeviceType.ANDROID_MOBILE
        assert "Android" in fp_android.user_agent
        assert fp_android.pixel_ratio >= 2.0  # Móviles tienen alta densidad
        
        # iOS
        assert fp_ios.device_type == DeviceType.IOS_MOBILE
        assert "iPhone" in fp_ios.user_agent
        assert fp_ios.pixel_ratio == 3.0
    
    def test_collision_detection(self):
        """Debe detectar y resolver colisiones de fingerprints"""
        manager = FingerprintManager()
        
        # Generar muchos fingerprints
        fps = [
            manager.generate_fingerprint(f"sat{i}", DeviceType.ANDROID_MOBILE)
            for i in range(50)
        ]
        
        # Verificar que no hay colisiones de canvas
        canvas_fps = [fp.canvas_fingerprint for fp in fps]
        assert len(canvas_fps) == len(set(canvas_fps))  # Todos únicos
        
        # Verificar que no hay colisiones de user-agent
        user_agents = [fp.user_agent for fp in fps]
        # Puede haber algunos duplicados en user-agents (es normal)
        # pero canvas debe ser único
    
    def test_geolocation_by_country(self):
        """Debe asignar coordenadas según país del proxy"""
        manager = FingerprintManager()
        
        fp_us = manager.generate_fingerprint("sat1", DeviceType.ANDROID_MOBILE, "US")
        fp_es = manager.generate_fingerprint("sat2", DeviceType.ANDROID_MOBILE, "ES")
        
        # US: ~37°N, -95°W
        assert fp_us.latitude is not None
        assert 30 < fp_us.latitude < 45
        assert -100 < fp_us.longitude < -90
        
        # España: ~40°N, -3°W
        assert fp_es.latitude is not None
        assert 35 < fp_es.latitude < 45
        assert -10 < fp_es.longitude < 5


# ============================================================================
# TESTS: AccountManager Integration
# ============================================================================

class TestAccountManagerIsolation:
    """Tests de integración AccountManager + Isolation"""
    
    def test_add_account_auto_isolation(self):
        """add_account debe configurar aislamiento automáticamente"""
        config = SatelliteConfig()
        manager = AccountManager(config)
        
        account = SatelliteAccount(
            account_id="sat1",
            username="test_sat",
            platform=PlatformType.TIKTOK,
            is_active=True
        )
        
        # Agregar con auto-isolation
        manager.add_account(account, auto_setup_isolation=True)
        
        # Verificar que tiene proxy y fingerprint
        assert account.proxy_config is not None
        assert account.gologin_profile_id is not None
        
        # Verificar que el proxy está en el router
        security_info = manager.get_account_security_info("sat1")
        assert security_info is not None
        assert security_info["proxy_url"] is not None
    
    def test_multiple_satellites_unique_isolation(self):
        """Múltiples satélites deben tener aislamiento único"""
        config = SatelliteConfig()
        manager = AccountManager(config)
        
        # Crear 3 satélites
        accounts = [
            SatelliteAccount(
                account_id=f"sat{i}",
                username=f"test_sat_{i}",
                platform=PlatformType.TIKTOK,
                is_active=True
            )
            for i in range(1, 4)
        ]
        
        # Agregar con auto-isolation
        for acc in accounts:
            manager.add_account(acc, auto_setup_isolation=True)
        
        # Verificar que todos tienen proxies únicos
        proxies = [acc.proxy_config["proxy_id"] for acc in accounts]
        assert len(proxies) == len(set(proxies))  # Todos únicos
        
        # Verificar que todos tienen fingerprints únicos
        fingerprints = [acc.gologin_profile_id for acc in accounts]
        assert len(fingerprints) == len(set(fingerprints))  # Todos únicos
    
    def test_validate_account_isolation(self):
        """validate_account_isolation debe detectar problemas"""
        config = SatelliteConfig()
        manager = AccountManager(config)
        
        account = SatelliteAccount(
            account_id="sat1",
            username="test_sat",
            platform=PlatformType.TIKTOK,
            is_active=True
        )
        
        # Agregar CON isolation
        manager.add_account(account, auto_setup_isolation=True)
        
        # Validar
        validations = manager.validate_account_isolation("sat1")
        
        # Todas las validaciones deben pasar
        assert validations["has_proxy"] is True
        assert validations["has_fingerprint"] is True
        assert validations["proxy_assigned"] is True
    
    def test_summary_includes_isolation_stats(self):
        """get_summary debe incluir estadísticas de aislamiento"""
        config = SatelliteConfig()
        manager = AccountManager(config)
        
        # Agregar cuentas
        for i in range(3):
            acc = SatelliteAccount(
                account_id=f"sat{i}",
                username=f"test_sat_{i}",
                platform=PlatformType.TIKTOK,
                is_active=True
            )
            manager.add_account(acc, auto_setup_isolation=True)
        
        summary = manager.get_summary()
        
        # Verificar que incluye stats de isolation
        assert "isolation" in summary
        assert summary["isolation"]["accounts_with_proxy"] == 3
        assert summary["isolation"]["accounts_with_fingerprint"] == 3
        assert summary["isolation"]["isolation_coverage"] > 0.9


# ============================================================================
# TESTS: TelegramBotIsolator
# ============================================================================

class TestTelegramBotIsolator:
    """Tests para TelegramBotProxyIsolator"""
    
    def test_setup_isolation_success(self):
        """setup_isolation debe configurar correctamente"""
        isolator = TelegramBotProxyIsolator("bot123456:ABC-TEST-TOKEN")
        
        success = isolator.setup_isolation()
        
        assert success is True
        assert isolator.config is not None
        assert isolator.config.is_isolated is True
    
    def test_bot_gets_vpn(self):
        """Bot debe recibir VPN exclusiva"""
        isolator = TelegramBotProxyIsolator("bot123456:ABC-TEST-TOKEN")
        isolator.setup_isolation()
        
        proxy_url = isolator.get_proxy_url()
        
        assert proxy_url is not None
        assert "telegram" in proxy_url.lower() or "vpn" in proxy_url.lower()
    
    def test_bot_gets_generic_pc_fingerprint(self):
        """Bot debe tener fingerprint Generic PC"""
        isolator = TelegramBotProxyIsolator("bot123456:ABC-TEST-TOKEN")
        isolator.setup_isolation()
        
        user_agent = isolator.get_user_agent()
        
        assert user_agent is not None
        assert "Windows" in user_agent or "Win" in user_agent
        assert "Mobile" not in user_agent  # NO debe ser móvil
    
    def test_validate_before_start(self):
        """validate_before_start debe verificar todo"""
        isolator = TelegramBotProxyIsolator("bot123456:ABC-TEST-TOKEN")
        isolator.setup_isolation()
        
        checks = isolator.validate_before_start()
        
        # Todas las validaciones deben pasar
        assert checks["isolation_configured"] is True
        assert checks["proxy_assigned"] is True
        assert checks["fingerprint_assigned"] is True
        assert checks["isolation_valid"] is True
    
    def test_get_isolation_info(self):
        """get_isolation_info debe retornar info completa"""
        isolator = TelegramBotProxyIsolator("bot123456:ABC-TEST-TOKEN")
        isolator.setup_isolation()
        
        info = isolator.get_isolation_info()
        
        assert "bot_id" in info
        assert "proxy" in info
        assert "fingerprint" in info
        assert "security_validations" in info
        
        # Proxy info
        assert info["proxy"]["type"] == "vpn"
        assert info["proxy"]["url"] is not None
        
        # Fingerprint info
        assert info["fingerprint"]["device_type"] == "generic_pc"
        assert info["fingerprint"]["user_agent"] is not None


# ============================================================================
# TESTS: End-to-End Isolation
# ============================================================================

class TestEndToEndIsolation:
    """Tests end-to-end de aislamiento completo"""
    
    def test_complete_isolation_setup(self):
        """Test completo: satélites + TelegramBot + validación"""
        
        # 1. Setup AccountManager con satélites
        config = SatelliteConfig()
        account_manager = AccountManager(config)
        
        # Crear 3 satélites
        for i in range(1, 4):
            acc = SatelliteAccount(
                account_id=f"sat{i}",
                username=f"test_sat_{i}",
                platform=PlatformType.TIKTOK,
                is_active=True
            )
            account_manager.add_account(acc, auto_setup_isolation=True)
        
        # 2. Setup TelegramBot
        bot_isolator = TelegramBotProxyIsolator("bot123:TEST")
        bot_isolator.setup_isolation()
        
        # 3. Obtener todos los proxies asignados
        sat_proxies = set()
        for i in range(1, 4):
            sec_info = account_manager.get_account_security_info(f"sat{i}")
            sat_proxies.add(sec_info["proxy_config"]["host"])
        
        bot_proxy = bot_isolator.config.proxy_config.host
        
        # 4. VALIDACIONES CRÍTICAS
        
        # Validación 1: Todos los satélites tienen proxies únicos
        assert len(sat_proxies) == 3, "Satellites must have unique proxies"
        
        # Validación 2: TelegramBot NO comparte IP con satélites
        assert bot_proxy not in sat_proxies, "TelegramBot MUST NOT share IP with satellites"
        
        # Validación 3: Todos tienen fingerprints
        for i in range(1, 4):
            sec_info = account_manager.get_account_security_info(f"sat{i}")
            assert sec_info["fingerprint_profile_id"] is not None
        
        bot_info = bot_isolator.get_isolation_info()
        assert bot_info["fingerprint"]["profile_id"] is not None
        
        # Validación 4: TelegramBot tiene fingerprint PC, satélites móvil
        assert bot_info["fingerprint"]["device_type"] == "generic_pc"
        
        for i in range(1, 4):
            sec_info = account_manager.get_account_security_info(f"sat{i}")
            fp = account_manager.fingerprint_manager.get_profile(f"sat{i}")
            assert fp.device_type in [DeviceType.ANDROID_MOBILE, DeviceType.IOS_MOBILE]
        
        # Validación 5: Política de aislamiento global
        proxy_router = account_manager.proxy_router
        policy_validations = proxy_router.validate_isolation_policy()
        
        assert policy_validations["no_shared_ips_satellites"] is True
        assert policy_validations["telegram_bot_isolated"] is True
        
        print("✅ End-to-end isolation test PASSED")
    
    def test_no_backend_ip_leakage(self):
        """Verificar que ningún componente usa backend IP por error"""
        
        # Setup
        config = SatelliteConfig()
        account_manager = AccountManager(config)
        
        acc = SatelliteAccount(
            account_id="sat1",
            username="test_sat",
            platform=PlatformType.TIKTOK,
            is_active=True
        )
        account_manager.add_account(acc, auto_setup_isolation=True)
        
        bot_isolator = TelegramBotProxyIsolator("bot123:TEST")
        bot_isolator.setup_isolation()
        
        # Obtener IPs
        sat_proxy_url = account_manager.get_account_security_info("sat1")["proxy_url"]
        bot_proxy_url = bot_isolator.get_proxy_url()
        
        # Verificar que NO son None (deben usar proxy)
        assert sat_proxy_url is not None, "Satellite MUST use proxy"
        assert bot_proxy_url is not None, "TelegramBot MUST use proxy"
        
        # Verificar que contienen hostname de proxy
        assert "example.com" in sat_proxy_url or "proxy" in sat_proxy_url
        assert "example.com" in bot_proxy_url or "vpn" in bot_proxy_url or "telegram" in bot_proxy_url


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
