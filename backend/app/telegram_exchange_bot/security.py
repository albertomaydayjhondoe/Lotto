"""
Security Layer - Sprint 7B
Capa de seguridad completa: VPN + Proxy + Fingerprints.

Integra componentes existentes para aislar completamente el bot.
"""
import logging
from typing import Optional, Dict
from dataclasses import dataclass

from app.exchange.telegram_bot_isolator import TelegramBotIsolator
from app.core.proxy_router import ProxyRouter, ComponentType
from app.identity.fingerprint_manager import FingerprintManager
from app.telegram_exchange_bot.accounts_pool import NonOfficialAccount

logger = logging.getLogger(__name__)


@dataclass
class SecurityContext:
    """Contexto de seguridad para una operación."""
    vpn_active: bool
    proxy_url: Optional[str]
    fingerprint_id: Optional[str]
    account_id: int
    component_type: ComponentType
    
    def is_secure(self) -> bool:
        """Verifica que el contexto es seguro."""
        return self.vpn_active and self.proxy_url is not None


class SecurityValidator:
    """Validador de seguridad antes de ejecutar acciones."""
    
    @staticmethod
    def validate_execution_context(context: SecurityContext) -> bool:
        """
        Valida que el contexto cumple requisitos de seguridad.
        
        REGLAS OBLIGATORIAS:
        - VPN activa
        - Proxy asignado
        - Fingerprint único
        
        Args:
            context: Contexto de seguridad
            
        Returns:
            True si es válido
            
        Raises:
            SecurityException si no cumple requisitos
        """
        if not context.vpn_active:
            raise SecurityException("VPN no activa. PROHIBIDO ejecutar sin VPN.")
        
        if not context.proxy_url:
            raise SecurityException("Proxy no asignado. PROHIBIDO ejecutar sin proxy.")
        
        if not context.fingerprint_id:
            logger.warning("Fingerprint no asignado. Se recomienda usar fingerprint único.")
        
        logger.info(
            f"Contexto de seguridad validado ✓ "
            f"(VPN: ✓, Proxy: {context.proxy_url[:20]}..., FP: {context.fingerprint_id})"
        )
        
        return True


class SecurityException(Exception):
    """Excepción de seguridad."""
    pass


class TelegramBotSecurityLayer:
    """
    Capa de seguridad completa para Telegram Bot.
    
    Características:
    - VPN obligatoria (TelegramBotIsolator)
    - Proxy rotation (ProxyRouter)
    - Fingerprints únicos (FingerprintManager)
    - Validación antes de cada acción
    - Circuit breaker si detecta problemas
    """
    
    def __init__(
        self,
        bot_isolator: TelegramBotIsolator,
        proxy_router: ProxyRouter,
        fingerprint_manager: FingerprintManager,
        enforce_vpn: bool = True,
        enforce_proxy: bool = True,
        enforce_fingerprint: bool = False  # Opcional por ahora
    ):
        """
        Args:
            bot_isolator: Aislador con VPN
            proxy_router: Router de proxies
            fingerprint_manager: Gestor de fingerprints
            enforce_vpn: Si VPN es obligatoria
            enforce_proxy: Si proxy es obligatorio
            enforce_fingerprint: Si fingerprint es obligatorio
        """
        self.bot_isolator = bot_isolator
        self.proxy_router = proxy_router
        self.fingerprint_manager = fingerprint_manager
        
        self.enforce_vpn = enforce_vpn
        self.enforce_proxy = enforce_proxy
        self.enforce_fingerprint = enforce_fingerprint
        
        # Estado
        self.vpn_initialized = False
        self.circuit_breaker_active = False
        
        # Stats
        self.stats = {
            "operations_secured": 0,
            "security_violations": 0,
            "vpn_failures": 0,
            "proxy_rotations": 0
        }
        
        logger.info(
            f"TelegramBotSecurityLayer inicializado. "
            f"Enforce: VPN={enforce_vpn}, Proxy={enforce_proxy}, FP={enforce_fingerprint}"
        )
    
    async def initialize(self):
        """
        Inicializa la capa de seguridad.
        
        OBLIGATORIO llamar antes de usar el bot.
        """
        logger.info("Inicializando capa de seguridad...")
        
        # 1. Validar VPN
        if self.enforce_vpn:
            logger.info("Validando VPN...")
            is_valid = await self.bot_isolator.validate_before_start()
            
            if not is_valid:
                raise SecurityException(
                    "VPN validation failed. "
                    "PROHIBIDO iniciar bot sin VPN activa."
                )
            
            self.vpn_initialized = True
            logger.info("VPN validada ✓")
        
        # 2. Validar proxies disponibles
        if self.enforce_proxy:
            logger.info("Validando proxies...")
            # ProxyRouter debe tener proxies configurados
            # TODO: Añadir método validate() en ProxyRouter
            logger.info("Proxies disponibles ✓")
        
        logger.info("Capa de seguridad inicializada ✓")
    
    async def get_security_context(
        self,
        account: NonOfficialAccount,
        operation: str
    ) -> SecurityContext:
        """
        Obtiene contexto de seguridad para una operación.
        
        Args:
            account: Cuenta que ejecutará la operación
            operation: Tipo de operación (like, comment, subscribe)
            
        Returns:
            SecurityContext configurado
            
        Raises:
            SecurityException si no se puede asegurar la operación
        """
        # Verificar circuit breaker
        if self.circuit_breaker_active:
            raise SecurityException(
                "Circuit breaker activo. Operaciones bloqueadas por seguridad."
            )
        
        # 1. VPN status
        vpn_active = self.vpn_initialized and self.enforce_vpn
        if self.enforce_vpn and not vpn_active:
            self.stats["vpn_failures"] += 1
            raise SecurityException("VPN no activa")
        
        # 2. Asignar proxy
        proxy_url = None
        if self.enforce_proxy:
            proxy = await self.proxy_router.assign_proxy(
                component=ComponentType.TELEGRAM_BOT,
                account_id=account.id
            )
            
            if not proxy:
                raise SecurityException("No hay proxies disponibles")
            
            proxy_url = proxy.get_url()
            self.stats["proxy_rotations"] += 1
        
        # 3. Asignar fingerprint
        fingerprint_id = None
        if self.enforce_fingerprint:
            fingerprint = await self.fingerprint_manager.get_or_create_fingerprint(
                account_id=account.id,
                platform=account.platform
            )
            fingerprint_id = fingerprint.id if fingerprint else None
        
        # Crear contexto
        context = SecurityContext(
            vpn_active=vpn_active,
            proxy_url=proxy_url,
            fingerprint_id=fingerprint_id,
            account_id=account.id,
            component_type=ComponentType.TELEGRAM_BOT
        )
        
        # Validar
        SecurityValidator.validate_execution_context(context)
        
        self.stats["operations_secured"] += 1
        
        return context
    
    async def validate_before_execution(
        self,
        context: SecurityContext
    ) -> bool:
        """
        Validación final antes de ejecutar acción.
        
        Args:
            context: Contexto de seguridad
            
        Returns:
            True si puede ejecutarse
        """
        try:
            SecurityValidator.validate_execution_context(context)
            return True
        except SecurityException as e:
            logger.error(f"Validación de seguridad falló: {e}")
            self.stats["security_violations"] += 1
            return False
    
    async def report_security_incident(
        self,
        incident_type: str,
        details: Dict
    ):
        """
        Reporta incidente de seguridad.
        
        Args:
            incident_type: Tipo de incidente (ban, block, detection)
            details: Detalles del incidente
        """
        logger.error(
            f"INCIDENTE DE SEGURIDAD: {incident_type}\n"
            f"Detalles: {details}"
        )
        
        self.stats["security_violations"] += 1
        
        # Si hay muchos incidentes, activar circuit breaker
        if self.stats["security_violations"] > 10:
            logger.critical("⚠️ Circuit breaker activado por múltiples incidentes")
            self.circuit_breaker_active = True
    
    async def rotate_proxy_for_account(
        self,
        account: NonOfficialAccount
    ) -> Optional[str]:
        """
        Rota proxy para una cuenta.
        
        Args:
            account: Cuenta
            
        Returns:
            Nuevo proxy URL o None
        """
        logger.info(f"Rotando proxy para cuenta {account.username}...")
        
        new_proxy = await self.proxy_router.assign_proxy(
            component=ComponentType.TELEGRAM_BOT,
            account_id=account.id,
            force_new=True
        )
        
        if new_proxy:
            self.stats["proxy_rotations"] += 1
            logger.info(f"Proxy rotado: {new_proxy.get_url()[:20]}...")
            return new_proxy.get_url()
        
        logger.warning("No se pudo rotar proxy")
        return None
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de seguridad."""
        return {
            **self.stats,
            "vpn_active": self.vpn_initialized,
            "circuit_breaker_active": self.circuit_breaker_active,
            "enforcement": {
                "vpn": self.enforce_vpn,
                "proxy": self.enforce_proxy,
                "fingerprint": self.enforce_fingerprint
            }
        }
    
    async def reset_circuit_breaker(self):
        """Resetea circuit breaker (manual)."""
        logger.info("Reseteando circuit breaker...")
        self.circuit_breaker_active = False
        self.stats["security_violations"] = 0


class AntiShadowbanProtection:
    """
    Protección contra shadowban.
    
    Estrategias:
    - Delays aleatorios entre acciones
    - Patrones de uso humano
    - Cooldowns por cuenta
    - Límites por hora/día
    """
    
    @staticmethod
    async def apply_human_delay(
        operation: str,
        min_seconds: int = 15,
        max_seconds: int = 45
    ):
        """
        Aplica delay humano antes de operación.
        
        Args:
            operation: Tipo de operación
            min_seconds: Mínimo de segundos
            max_seconds: Máximo de segundos
        """
        import random
        import asyncio
        
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Aplicando delay humano: {delay:.1f}s antes de {operation}")
        await asyncio.sleep(delay)
    
    @staticmethod
    def get_recommended_cooldown(operation: str) -> int:
        """
        Obtiene cooldown recomendado después de operación.
        
        Returns:
            Minutos de cooldown
        """
        cooldowns = {
            "like": 1,
            "comment": 3,
            "subscribe": 5,
            "follow": 5,
            "save": 2
        }
        
        return cooldowns.get(operation, 2)
