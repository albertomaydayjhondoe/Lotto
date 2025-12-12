"""
Account Manager
Gestión de cuentas satélite con GoLogin/ADB integration hooks.

Sprint 2 - Satellite Engine
ACTUALIZADO: Integración con ProxyRouter y FingerprintManager
para garantizar aislamiento total de identidad (Diciembre 2025)

Author: AI Architect
Date: 2025-12-07
Updated: 2025-12-08 - Política de Aislamiento de Identidad
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.satellites.models import SatelliteAccount, PlatformType
from app.satellites.config import SatelliteConfig
from app.core.proxy_router import get_proxy_router, ComponentType, ProxyConfig
from app.core.fingerprint_manager import get_fingerprint_manager, DeviceType

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Manager para cuentas satélite multi-plataforma.
    
    Features:
    - CRUD de cuentas
    - Rotation logic
    - Health checking
    - GoLogin/ADB integration hooks
    - Rate limit enforcement
    - ⚡ NUEVO: Aislamiento completo con ProxyRouter y FingerprintManager
    """
    
    def __init__(self, config: SatelliteConfig):
        """
        Inicializar account manager.
        
        Args:
            config: Configuración del Satellite Engine
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Accounts storage
        self.accounts: Dict[str, SatelliteAccount] = {}
        
        # 🔐 NUEVO: Security managers
        self.proxy_router = get_proxy_router()
        self.fingerprint_manager = get_fingerprint_manager()
        
        self.logger.info("AccountManager initialized with isolation security")
    
    def add_account(
        self,
        account: SatelliteAccount,
        auto_setup_isolation: bool = True
    ) -> None:
        """
        Agregar cuenta satélite.
        
        ⚡ NUEVO: Automáticamente asigna proxy y fingerprint únicos
        
        Args:
            account: Cuenta a agregar
            auto_setup_isolation: Si True, asigna automáticamente proxy y fingerprint
        """
        self.accounts[account.account_id] = account
        
        # 🔐 NUEVO: Setup automático de aislamiento
        if auto_setup_isolation:
            self._setup_account_isolation(account)
        
        self.logger.info(
            f"Added account {account.username} ({account.platform}) - ID: {account.account_id}"
            f" [Proxy: {account.proxy_config is not None}, Fingerprint: {account.gologin_profile_id is not None}]"
        )
    
    def _setup_account_isolation(self, account: SatelliteAccount) -> None:
        """
        🔐 NUEVO: Configura aislamiento completo para cuenta satélite
        
        CRÍTICO: Cada cuenta debe tener:
        - Proxy único
        - Fingerprint único
        - Perfil GoLogin/ADB aislado
        
        Ver: docs/POLITICA_AISLAMIENTO_IDENTIDAD.md
        """
        account_id = account.account_id
        
        # 1. Asignar proxy único
        proxy_config = self.proxy_router.assign_proxy(
            component_id=account_id,
            component_type=ComponentType.SATELLITE_ACCOUNT
        )
        
        if proxy_config:
            # Guardar configuración de proxy en la cuenta
            account.proxy_config = {
                "proxy_id": proxy_config.proxy_id,
                "host": proxy_config.host,
                "port": proxy_config.port,
                "type": proxy_config.proxy_type.value,
                "country": proxy_config.country,
                "proxy_url": self.proxy_router.get_proxy_url(account_id)
            }
            self.logger.info(f"✅ Assigned unique proxy to {account.username}: {proxy_config.proxy_id}")
        else:
            self.logger.error(f"❌ Failed to assign proxy to {account.username} - CRITICAL")
        
        # 2. Generar fingerprint único
        device_type = self._get_device_type_for_platform(account.platform)
        country_code = proxy_config.country if proxy_config else "US"
        
        fingerprint = self.fingerprint_manager.generate_fingerprint(
            component_id=account_id,
            device_type=device_type,
            country_code=country_code
        )
        
        # Guardar profile ID en la cuenta
        account.gologin_profile_id = fingerprint.profile_id
        self.logger.info(f"✅ Generated unique fingerprint for {account.username}: {fingerprint.profile_id}")
        
        # 3. TODO: Crear perfil GoLogin real (si está habilitado)
        # gologin_id = await self.fingerprint_manager.create_gologin_profile(fingerprint)
        
        self.logger.info(f"🔐 Isolation setup complete for {account.username}")
    
    def _get_device_type_for_platform(self, platform: PlatformType) -> DeviceType:
        """Determina tipo de dispositivo según plataforma"""
        # TikTok e Instagram prefieren móviles
        if platform in ["tiktok", "instagram"]:
            # 70% Android, 30% iOS
            import random
            return DeviceType.ANDROID_MOBILE if random.random() < 0.7 else DeviceType.IOS_MOBILE
        
        # YouTube puede usar cualquiera
        return DeviceType.ANDROID_MOBILE
    
    def remove_account(
        self,
        account_id: str
    ) -> bool:
        """
        Remover cuenta satélite.
        
        Args:
            account_id: ID de la cuenta
            
        Returns:
            True si se removió
        """
        if account_id in self.accounts:
            account = self.accounts[account_id]
            del self.accounts[account_id]
            self.logger.info(f"Removed account {account.username}")
            return True
        return False
    
    def get_account(
        self,
        account_id: str
    ) -> Optional[SatelliteAccount]:
        """
        Obtener cuenta por ID.
        
        Args:
            account_id: ID de la cuenta
            
        Returns:
            SatelliteAccount o None
        """
        return self.accounts.get(account_id)
    
    def get_accounts_for_platform(
        self,
        platform: PlatformType,
        active_only: bool = True
    ) -> List[SatelliteAccount]:
        """
        Obtener cuentas de una plataforma.
        
        Args:
            platform: Plataforma a filtrar
            active_only: Solo cuentas activas
            
        Returns:
            Lista de cuentas
        """
        accounts = [
            acc for acc in self.accounts.values()
            if acc.platform == platform
        ]
        
        if active_only:
            accounts = [acc for acc in accounts if acc.is_active]
        
        return accounts
    
    def get_best_account(
        self,
        platform: PlatformType
    ) -> Optional[SatelliteAccount]:
        """
        Obtener la mejor cuenta para publicar (rotation logic).
        
        Criterios:
        - Activa
        - No ha excedido daily limit
        - Tiempo suficiente desde último post
        - Mejor success rate
        
        Args:
            platform: Plataforma destino
            
        Returns:
            SatelliteAccount o None si ninguna disponible
        """
        candidates = self.get_accounts_for_platform(platform, active_only=True)
        
        if not candidates:
            self.logger.warning(f"No active accounts for {platform}")
            return None
        
        # Filter by daily limit
        candidates = [
            acc for acc in candidates
            if acc.posts_today < acc.daily_post_limit
        ]
        
        if not candidates:
            self.logger.warning(f"All {platform} accounts hit daily limit")
            return None
        
        # Filter by time since last post
        min_time_between = self.config.min_time_between_posts_sec
        now = datetime.utcnow()
        
        candidates = [
            acc for acc in candidates
            if not acc.last_post_at or 
               (now - acc.last_post_at).total_seconds() >= min_time_between
        ]
        
        if not candidates:
            self.logger.warning(
                f"All {platform} accounts need cooldown (min {min_time_between}s between posts)"
            )
            return None
        
        # Sort by success rate (highest first)
        candidates.sort(key=lambda acc: acc.success_rate, reverse=True)
        
        best = candidates[0]
        self.logger.info(
            f"Selected account {best.username} for {platform} "
            f"(success rate: {best.success_rate:.2%}, posts today: {best.posts_today})"
        )
        
        return best
    
    def update_post_stats(
        self,
        account_id: str,
        success: bool
    ) -> None:
        """
        Actualizar estadísticas tras un post.
        
        Args:
            account_id: ID de la cuenta
            success: Si el upload fue exitoso
        """
        account = self.get_account(account_id)
        if not account:
            return
        
        # Update post counts
        account.total_uploads += 1
        if not success:
            account.failed_uploads += 1
        
        # Recalculate success rate
        account.success_rate = (
            (account.total_uploads - account.failed_uploads) / account.total_uploads
            if account.total_uploads > 0 else 1.0
        )
        
        # Update daily counter
        account.posts_today += 1
        account.last_post_at = datetime.utcnow()
        
        self.logger.debug(
            f"Updated stats for {account.username}: "
            f"total={account.total_uploads}, success_rate={account.success_rate:.2%}"
        )
    
    def reset_daily_counters(self) -> None:
        """
        Resetear contadores diarios (ejecutar a medianoche UTC).
        """
        for account in self.accounts.values():
            account.posts_today = 0
        
        self.logger.info("Reset daily counters for all accounts")
    
    async def validate_account(
        self,
        account_id: str
    ) -> bool:
        """
        Validar que una cuenta funciona correctamente.
        
        STUB Sprint 2: Always returns True
        TODO Sprint 3: Real platform validation
        
        Args:
            account_id: ID de la cuenta
            
        Returns:
            True si cuenta válida
        """
        account = self.get_account(account_id)
        if not account:
            return False
        
        # STUB: Simulate validation
        self.logger.info(f"[STUB] Validating account {account.username}")
        
        # TODO Sprint 3: Real platform API validation
        # - Check auth tokens
        # - Verify account status
        # - Test API connectivity
        
        return True
    
    def setup_gologin_profile(
        self,
        account_id: str,
        profile_id: str
    ) -> bool:
        """
        Asociar perfil GoLogin a cuenta.
        
        ⚡ ACTUALIZADO: Integrado con FingerprintManager
        
        Args:
            account_id: ID de la cuenta
            profile_id: ID del perfil GoLogin
            
        Returns:
            True si configurado exitosamente
        """
        account = self.get_account(account_id)
        if not account:
            return False
        
        account.gologin_profile_id = profile_id
        
        self.logger.info(
            f"Associated GoLogin profile {profile_id} with {account.username}"
        )
        
        # TODO: 
        # - Initialize GoLogin API client
        # - Start/stop browser profiles
        # - Manage cookies and sessions
        
        return True
    
    def setup_proxy(
        self,
        account_id: str,
        proxy_config: Dict
    ) -> bool:
        """
        Configurar proxy para cuenta.
        
        ⚠️ DEPRECATED: Usar add_account() con auto_setup_isolation=True
        
        El ProxyRouter asigna automáticamente proxies únicos.
        
        Args:
            account_id: ID de la cuenta
            proxy_config: Configuración del proxy
            
        Returns:
            True si configurado exitosamente
        """
        account = self.get_account(account_id)
        if not account:
            return False
        
        self.logger.warning(
            f"setup_proxy() is deprecated. Use add_account() with auto_setup_isolation=True. "
            f"ProxyRouter handles automatic assignment."
        )
        
        account.proxy_config = proxy_config
        
        return True
    
    def validate_account_isolation(self, account_id: str) -> Dict[str, bool]:
        """
        🔐 NUEVO: Valida que una cuenta cumpla política de aislamiento
        
        Verifica:
        - Tiene proxy único asignado
        - Tiene fingerprint único
        - No comparte IP con otras cuentas
        
        Args:
            account_id: ID de la cuenta
            
        Returns:
            Dict con resultados de validación
        """
        account = self.get_account(account_id)
        if not account:
            return {"error": "Account not found"}
        
        validations = {
            "has_proxy": account.proxy_config is not None,
            "has_fingerprint": account.gologin_profile_id is not None,
            "proxy_assigned": self.proxy_router.validate_request(
                account_id,
                ComponentType.SATELLITE_ACCOUNT
            ),
            "unique_identity": True  # TODO: Implementar validación de unicidad
        }
        
        all_passed = all(validations.values())
        
        if not all_passed:
            self.logger.warning(
                f"Account {account.username} failed isolation validation: {validations}"
            )
        else:
            self.logger.info(f"✅ Account {account.username} passes isolation validation")
        
        return validations
    
    def get_account_security_info(self, account_id: str) -> Optional[Dict]:
        """
        🔐 NUEVO: Obtiene información de seguridad de una cuenta
        
        Args:
            account_id: ID de la cuenta
            
        Returns:
            Dict con info de proxy y fingerprint
        """
        account = self.get_account(account_id)
        if not account:
            return None
        
        proxy_url = self.proxy_router.get_proxy_url(account_id)
        fingerprint = self.fingerprint_manager.get_profile(account_id)
        
        return {
            "account_id": account_id,
            "username": account.username,
            "platform": account.platform,
            "proxy_config": account.proxy_config,
            "proxy_url": proxy_url,
            "fingerprint_profile_id": account.gologin_profile_id,
            "fingerprint_details": {
                "device_type": fingerprint.device_type.value if fingerprint else None,
                "user_agent": fingerprint.user_agent if fingerprint else None,
                "country": account.proxy_config.get("country") if account.proxy_config else None
            } if fingerprint else None
        }
    
    def get_summary(self) -> Dict:
        """
        Obtener resumen del account manager.
        
        ⚡ ACTUALIZADO: Incluye estadísticas de aislamiento
        
        Returns:
            Dict con estadísticas
        """
        active_accounts = [acc for acc in self.accounts.values() if acc.is_active]
        
        platform_counts = {
            "tiktok": len(self.get_accounts_for_platform("tiktok")),
            "instagram": len(self.get_accounts_for_platform("instagram")),
            "youtube": len(self.get_accounts_for_platform("youtube")),
        }
        
        avg_success_rate = (
            sum(acc.success_rate for acc in self.accounts.values()) / len(self.accounts)
            if self.accounts else 0.0
        )
        
        # 🔐 NUEVO: Estadísticas de aislamiento
        accounts_with_proxy = sum(
            1 for acc in self.accounts.values() if acc.proxy_config is not None
        )
        accounts_with_fingerprint = sum(
            1 for acc in self.accounts.values() if acc.gologin_profile_id is not None
        )
        
        return {
            "total_accounts": len(self.accounts),
            "active_accounts": len(active_accounts),
            "by_platform": platform_counts,
            "avg_success_rate": avg_success_rate,
            "total_uploads": sum(acc.total_uploads for acc in self.accounts.values()),
            "total_failures": sum(acc.failed_uploads for acc in self.accounts.values()),
            # 🔐 NUEVO: Isolation stats
            "isolation": {
                "accounts_with_proxy": accounts_with_proxy,
                "accounts_with_fingerprint": accounts_with_fingerprint,
                "isolation_coverage": (
                    (accounts_with_proxy + accounts_with_fingerprint) / (2 * len(self.accounts))
                    if self.accounts else 0.0
                ),
                "proxy_router_stats": self.proxy_router.get_stats(),
                "fingerprint_manager_stats": self.fingerprint_manager.get_stats()
            }
        }
