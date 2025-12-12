"""
🤖 TELEGRAM BOT PROXY ISOLATOR

Este módulo gestiona el aislamiento del TelegramBot Exchange Engine.

CRÍTICO: El TelegramBot debe tener:
- VPN EXCLUSIVA (diferente de todo)
- Fingerprint NEUTRAL (Generic PC)
- Entorno aislado (Docker/VM)
- NUNCA compartir IP con satélites o backend

El TelegramBot forma parte del ecosistema de INTERCAMBIOS HUMANOS,
por lo que debe aparecer como una persona real usando Telegram, 
NO como actividad automatizada.

Autor: STAKAZO Security Team
Fecha: Diciembre 2025
Versión: 1.0.0
"""

import os
import logging
from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from app.core.proxy_router import get_proxy_router, ComponentType, ProxyConfig
from app.core.fingerprint_manager import get_fingerprint_manager, DeviceType


logger = logging.getLogger(__name__)


class TelegramBotConfig(BaseModel):
    """Configuración del TelegramBot con aislamiento"""
    bot_token: str
    bot_username: str
    proxy_config: Optional[ProxyConfig] = None
    fingerprint_profile_id: Optional[str] = None
    is_isolated: bool = False
    isolation_setup_at: Optional[datetime] = None


class TelegramBotProxyIsolator:
    """
    Isolator para TelegramBot Exchange Engine
    
    Garantiza que el bot:
    1. Use VPN exclusiva (nunca backend IP, nunca satélites)
    2. Tenga fingerprint neutral (Generic PC, no móvil)
    3. No se correlacione con actividad automatizada
    4. Parezca una persona real usando Telegram
    """
    
    def __init__(self, bot_token: str):
        """
        Inicializa isolator para TelegramBot
        
        Args:
            bot_token: Token del bot de Telegram
        """
        self.bot_token = bot_token
        self.bot_username = self._extract_bot_username(bot_token)
        self.bot_id = f"telegram_exchange_bot_{self.bot_username}"
        
        self.proxy_router = get_proxy_router()
        self.fingerprint_manager = get_fingerprint_manager()
        
        self.config: Optional[TelegramBotConfig] = None
        
        self.logger = logging.getLogger(__name__)
    
    def _extract_bot_username(self, token: str) -> str:
        """Extrae username del bot desde token"""
        # Token format: bot123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
        bot_id = token.split(":")[0].replace("bot", "")
        return f"bot_{bot_id[:8]}"
    
    def setup_isolation(self) -> bool:
        """
        🔐 Configura aislamiento completo del TelegramBot
        
        CRÍTICO: Debe ejecutarse ANTES de iniciar el bot
        
        Returns:
            True si setup exitoso
        """
        
        self.logger.info(f"🔐 Setting up isolation for TelegramBot {self.bot_username}")
        
        # 1. Asignar VPN exclusiva
        proxy_config = self.proxy_router.assign_proxy(
            component_id=self.bot_id,
            component_type=ComponentType.TELEGRAM_BOT,
            force_new=False
        )
        
        if not proxy_config:
            self.logger.error(
                f"❌ CRITICAL: Failed to assign VPN to TelegramBot. "
                f"Bot CANNOT start without isolation. "
                f"See: docs/POLITICA_AISLAMIENTO_IDENTIDAD.md"
            )
            return False
        
        self.logger.info(f"✅ Assigned exclusive VPN to TelegramBot: {proxy_config.proxy_id}")
        
        # 2. Generar fingerprint NEUTRAL (Generic PC)
        fingerprint = self.fingerprint_manager.generate_fingerprint(
            component_id=self.bot_id,
            device_type=DeviceType.GENERIC_PC,  # CRÍTICO: Generic PC, no móvil
            country_code=proxy_config.country
        )
        
        self.logger.info(
            f"✅ Generated neutral fingerprint for TelegramBot: {fingerprint.profile_id} "
            f"(Device: {fingerprint.device_type.value})"
        )
        
        # 3. Validar aislamiento
        if not self._validate_isolation():
            self.logger.error(
                f"❌ CRITICAL: TelegramBot isolation validation FAILED. "
                f"Bot may be using shared IP or fingerprint."
            )
            return False
        
        # 4. Guardar configuración
        self.config = TelegramBotConfig(
            bot_token=self.bot_token,
            bot_username=self.bot_username,
            proxy_config=proxy_config,
            fingerprint_profile_id=fingerprint.profile_id,
            is_isolated=True,
            isolation_setup_at=datetime.utcnow()
        )
        
        self.logger.info(f"🔐 ✅ TelegramBot isolation setup COMPLETE")
        self.logger.info(f"   - VPN: {proxy_config.proxy_id} ({proxy_config.country})")
        self.logger.info(f"   - Fingerprint: {fingerprint.profile_id} ({fingerprint.device_type.value})")
        self.logger.info(f"   - User-Agent: {fingerprint.user_agent[:50]}...")
        
        return True
    
    def _validate_isolation(self) -> bool:
        """
        Valida que el bot esté correctamente aislado
        
        Returns:
            True si pasa todas las validaciones
        """
        
        validations = {
            "has_proxy": False,
            "proxy_is_vpn": False,
            "has_fingerprint": False,
            "fingerprint_is_pc": False,
            "not_using_backend_ip": True,
            "not_sharing_satellite_ip": True
        }
        
        # 1. Verificar proxy asignado
        proxy_config = self.proxy_router.assignments.get(self.bot_id)
        if proxy_config:
            validations["has_proxy"] = True
            validations["proxy_is_vpn"] = proxy_config.proxy_config.proxy_type.value == "vpn"
        
        # 2. Verificar fingerprint
        fingerprint = self.fingerprint_manager.get_profile(self.bot_id)
        if fingerprint:
            validations["has_fingerprint"] = True
            validations["fingerprint_is_pc"] = fingerprint.device_type == DeviceType.GENERIC_PC
        
        # 3. Verificar que no comparte IP con satélites
        # (esto se verifica en ProxyRouter)
        isolation_policy = self.proxy_router.validate_isolation_policy()
        validations["not_sharing_satellite_ip"] = isolation_policy.get("telegram_bot_isolated", False)
        
        all_passed = all(validations.values())
        
        if not all_passed:
            self.logger.error(f"❌ Isolation validation failed: {validations}")
        else:
            self.logger.info(f"✅ All isolation validations passed")
        
        return all_passed
    
    def get_proxy_url(self) -> Optional[str]:
        """
        Obtiene URL del proxy/VPN para configurar el bot
        
        Returns:
            URL del proxy o None si no configurado
        """
        if not self.config or not self.config.is_isolated:
            self.logger.warning("TelegramBot not isolated. Call setup_isolation() first.")
            return None
        
        return self.proxy_router.get_proxy_url(self.bot_id)
    
    def get_user_agent(self) -> Optional[str]:
        """
        Obtiene User-Agent del fingerprint
        
        Returns:
            User-Agent string
        """
        fingerprint = self.fingerprint_manager.get_profile(self.bot_id)
        return fingerprint.user_agent if fingerprint else None
    
    def validate_before_start(self) -> Dict[str, bool]:
        """
        Validación PRE-START del bot
        
        CRÍTICO: Debe ejecutarse y pasar ANTES de iniciar el bot
        
        Returns:
            Dict con validaciones
        """
        
        checks = {
            "isolation_configured": self.config is not None and self.config.is_isolated,
            "proxy_assigned": self.get_proxy_url() is not None,
            "fingerprint_assigned": self.get_user_agent() is not None,
            "isolation_valid": self._validate_isolation()
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            self.logger.info("✅ All pre-start checks passed. Bot can start safely.")
        else:
            self.logger.error(
                f"❌ Pre-start checks FAILED: {checks}\n"
                f"   Bot MUST NOT start until all checks pass."
            )
        
        return checks
    
    def report_activity(self, activity_type: str, success: bool):
        """
        Reporta actividad del bot (para estadísticas de proxy)
        
        Args:
            activity_type: Tipo de actividad (message, command, interaction)
            success: Si fue exitosa
        """
        self.proxy_router.report_proxy_status(
            self.bot_id,
            success=success
        )
    
    def get_isolation_info(self) -> Dict:
        """
        Obtiene información completa de aislamiento
        
        Returns:
            Dict con toda la info de seguridad
        """
        if not self.config:
            return {"error": "Not configured"}
        
        fingerprint = self.fingerprint_manager.get_profile(self.bot_id)
        
        return {
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "is_isolated": self.config.is_isolated,
            "isolation_setup_at": self.config.isolation_setup_at.isoformat() if self.config.isolation_setup_at else None,
            "proxy": {
                "proxy_id": self.config.proxy_config.proxy_id if self.config.proxy_config else None,
                "type": self.config.proxy_config.proxy_type.value if self.config.proxy_config else None,
                "country": self.config.proxy_config.country if self.config.proxy_config else None,
                "url": self.get_proxy_url()
            },
            "fingerprint": {
                "profile_id": self.config.fingerprint_profile_id,
                "device_type": fingerprint.device_type.value if fingerprint else None,
                "browser": fingerprint.browser_type.value if fingerprint else None,
                "platform": fingerprint.platform if fingerprint else None,
                "user_agent": fingerprint.user_agent if fingerprint else None
            },
            "security_validations": self.validate_before_start()
        }


def create_isolated_telegram_bot(bot_token: str) -> TelegramBotProxyIsolator:
    """
    Factory function para crear TelegramBot con aislamiento
    
    Args:
        bot_token: Token del bot
        
    Returns:
        TelegramBotProxyIsolator configurado
    """
    isolator = TelegramBotProxyIsolator(bot_token)
    
    if not isolator.setup_isolation():
        raise RuntimeError(
            "Failed to setup TelegramBot isolation. "
            "Bot CANNOT start without proper isolation. "
            "Check logs and docs/POLITICA_AISLAMIENTO_IDENTIDAD.md"
        )
    
    return isolator
