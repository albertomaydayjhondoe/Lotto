"""
Accounts Pool - Sprint 7B
Gestión de cuentas NO oficiales para ejecutar interacciones.

REGLA CRÍTICA: Estas cuentas SOLO dan apoyo (likes/comments/subs).
NUNCA reciben apoyo hacia ellas. El apoyo se pide hacia cuentas OFICIALES.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.telegram_exchange_bot.models import AccountRole
from app.identity.account_manager import AccountManager
from app.core.proxy_router import ProxyRouter, ComponentType

logger = logging.getLogger(__name__)


class AccountStatus(str, Enum):
    """Estado de una cuenta NO oficial."""
    ACTIVE = "active"              # Activa y lista para usar
    WARMING_UP = "warming_up"      # En proceso de warm-up
    COOLDOWN = "cooldown"          # En cooldown (usada recientemente)
    BLOCKED = "blocked"            # Bloqueada/baneada
    SUSPENDED = "suspended"        # Suspendida temporalmente
    MAINTENANCE = "maintenance"    # En mantenimiento


class AccountHealth(str, Enum):
    """Salud de una cuenta."""
    HEALTHY = "healthy"            # >90% success rate
    DEGRADED = "degraded"          # 50-90% success rate
    UNHEALTHY = "unhealthy"        # <50% success rate
    UNKNOWN = "unknown"            # Sin suficientes datos


@dataclass
class NonOfficialAccount:
    """
    Cuenta NO oficial para ejecutar interacciones.
    
    IMPORTANTE: Esta cuenta da apoyo, NO lo recibe.
    """
    id: int
    platform: str                  # youtube, instagram, tiktok
    username: str
    email: Optional[str]
    password: Optional[str]
    access_token: Optional[str]
    
    # Estado
    status: AccountStatus
    health: AccountHealth
    
    # Métricas
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime = None
    
    # Rate limiting
    interactions_today: int = 0
    interactions_this_hour: int = 0
    
    # Proxy asociado
    proxy_id: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def success_rate(self) -> float:
        """Calcula tasa de éxito."""
        if self.total_interactions == 0:
            return 0.0
        return self.successful_interactions / self.total_interactions
    
    @property
    def is_available(self) -> bool:
        """Verifica si está disponible para usar."""
        return self.status == AccountStatus.ACTIVE and self.health != AccountHealth.UNHEALTHY
    
    @property
    def needs_cooldown(self) -> bool:
        """Verifica si necesita cooldown."""
        if not self.last_used_at:
            return False
        
        # Cooldown de 30 min después de cada uso
        time_since_use = datetime.utcnow() - self.last_used_at
        return time_since_use < timedelta(minutes=30)


class AccountHealthMonitor:
    """Monitor de salud de cuentas."""
    
    @staticmethod
    def check_health(account: NonOfficialAccount) -> AccountHealth:
        """
        Evalúa salud de la cuenta.
        
        Returns:
            AccountHealth
        """
        if account.total_interactions < 10:
            return AccountHealth.UNKNOWN
        
        success_rate = account.success_rate
        
        if success_rate >= 0.9:
            return AccountHealth.HEALTHY
        elif success_rate >= 0.5:
            return AccountHealth.DEGRADED
        else:
            return AccountHealth.UNHEALTHY
    
    @staticmethod
    def should_suspend(account: NonOfficialAccount) -> bool:
        """Determina si debe suspenderse la cuenta."""
        # Suspender si hay muchos fallos consecutivos
        if account.failed_interactions >= 5 and account.success_rate < 0.3:
            return True
        
        # Suspender si está en unhealthy con muchas interacciones
        if account.health == AccountHealth.UNHEALTHY and account.total_interactions > 20:
            return True
        
        return False


class AccountRotationStrategy:
    """Estrategia de rotación de cuentas."""
    
    @staticmethod
    def select_account(
        accounts: List[NonOfficialAccount],
        platform: str
    ) -> Optional[NonOfficialAccount]:
        """
        Selecciona cuenta óptima para usar.
        
        Criterios:
        1. Plataforma correcta
        2. Estado ACTIVE
        3. Sin cooldown
        4. Health HEALTHY o DEGRADED
        5. Menos usada recientemente
        
        Args:
            accounts: Lista de cuentas
            platform: Plataforma requerida
            
        Returns:
            Cuenta seleccionada o None
        """
        # Filtrar por plataforma y disponibilidad
        eligible = [
            acc for acc in accounts
            if acc.platform == platform
            and acc.is_available
            and not acc.needs_cooldown
        ]
        
        if not eligible:
            logger.warning(f"No hay cuentas disponibles para {platform}")
            return None
        
        # Priorizar por salud
        healthy = [acc for acc in eligible if acc.health == AccountHealth.HEALTHY]
        if healthy:
            # Seleccionar la menos usada
            return min(healthy, key=lambda a: a.interactions_today)
        
        degraded = [acc for acc in eligible if acc.health == AccountHealth.DEGRADED]
        if degraded:
            return min(degraded, key=lambda a: a.interactions_today)
        
        # Fallback a cualquier elegible
        return min(eligible, key=lambda a: a.interactions_today)


class NonOfficialAccountsPool:
    """
    Pool de cuentas NO oficiales.
    
    Características:
    - Gestión de cuentas por plataforma
    - Health monitoring
    - Rotación inteligente
    - Warm-up de nuevas cuentas
    - Rate limiting automático
    """
    
    def __init__(
        self,
        db: Session,
        account_manager: AccountManager,
        proxy_router: ProxyRouter,
        max_interactions_per_account_day: int = 50,
        max_interactions_per_account_hour: int = 10
    ):
        """
        Args:
            db: Sesión de BD
            account_manager: Gestor de cuentas (sistema existente)
            proxy_router: Router de proxies
            max_interactions_per_account_day: Límite diario por cuenta
            max_interactions_per_account_hour: Límite horario por cuenta
        """
        self.db = db
        self.account_manager = account_manager
        self.proxy_router = proxy_router
        self.max_per_day = max_interactions_per_account_day
        self.max_per_hour = max_interactions_per_account_hour
        
        # Pool interno
        self.accounts: Dict[str, List[NonOfficialAccount]] = {
            "youtube": [],
            "instagram": [],
            "tiktok": []
        }
        
        # Estadísticas
        self.stats = {
            "total_accounts": 0,
            "active_accounts": 0,
            "blocked_accounts": 0,
            "interactions_today": 0
        }
        
        logger.info(
            f"NonOfficialAccountsPool inicializado. "
            f"Límites: {max_interactions_per_account_day}/día, {max_interactions_per_account_hour}/hora"
        )
    
    async def load_accounts(self):
        """Carga cuentas NO oficiales desde BD."""
        logger.info("Cargando cuentas NO oficiales...")
        
        # TODO: Cargar desde BD usando AccountManager
        # Por ahora, crear cuentas dummy para desarrollo
        
        # Simulación de cuentas (reemplazar con BD real)
        dummy_accounts = [
            NonOfficialAccount(
                id=1,
                platform="youtube",
                username="fan_account_1",
                email="fan1@example.com",
                password="encrypted_pass",
                access_token=None,
                status=AccountStatus.ACTIVE,
                health=AccountHealth.HEALTHY
            ),
            NonOfficialAccount(
                id=2,
                platform="youtube",
                username="fan_account_2",
                email="fan2@example.com",
                password="encrypted_pass",
                access_token=None,
                status=AccountStatus.ACTIVE,
                health=AccountHealth.HEALTHY
            ),
            NonOfficialAccount(
                id=3,
                platform="instagram",
                username="fan_ig_1",
                email="fanig1@example.com",
                password="encrypted_pass",
                access_token=None,
                status=AccountStatus.ACTIVE,
                health=AccountHealth.HEALTHY
            ),
        ]
        
        # Organizar por plataforma
        for account in dummy_accounts:
            self.accounts[account.platform].append(account)
        
        self._update_stats()
        
        logger.info(
            f"Cuentas cargadas: YT={len(self.accounts['youtube'])}, "
            f"IG={len(self.accounts['instagram'])}, TT={len(self.accounts['tiktok'])}"
        )
    
    async def get_account(self, platform: str) -> Optional[NonOfficialAccount]:
        """
        Obtiene cuenta disponible para la plataforma.
        
        Args:
            platform: youtube, instagram, tiktok
            
        Returns:
            NonOfficialAccount o None
        """
        platform = platform.lower()
        
        if platform not in self.accounts:
            logger.error(f"Plataforma desconocida: {platform}")
            return None
        
        # Seleccionar cuenta usando estrategia de rotación
        account = AccountRotationStrategy.select_account(
            self.accounts[platform],
            platform
        )
        
        if not account:
            logger.warning(f"No hay cuentas disponibles para {platform}")
            return None
        
        # Verificar rate limits
        if not self._check_rate_limits(account):
            logger.warning(f"Cuenta {account.username} excedió rate limits")
            return None
        
        logger.info(f"Cuenta seleccionada: {account.username} ({platform})")
        return account
    
    def _check_rate_limits(self, account: NonOfficialAccount) -> bool:
        """Verifica rate limits de la cuenta."""
        if account.interactions_today >= self.max_per_day:
            return False
        
        if account.interactions_this_hour >= self.max_per_hour:
            return False
        
        return True
    
    async def mark_used(
        self,
        account: NonOfficialAccount,
        success: bool
    ):
        """
        Marca cuenta como usada y actualiza stats.
        
        Args:
            account: Cuenta utilizada
            success: Si la interacción fue exitosa
        """
        account.last_used_at = datetime.utcnow()
        account.total_interactions += 1
        account.interactions_today += 1
        account.interactions_this_hour += 1
        
        if success:
            account.successful_interactions += 1
        else:
            account.failed_interactions += 1
        
        # Actualizar salud
        account.health = AccountHealthMonitor.check_health(account)
        
        # Verificar si debe suspenderse
        if AccountHealthMonitor.should_suspend(account):
            account.status = AccountStatus.SUSPENDED
            logger.warning(f"Cuenta {account.username} suspendida (baja salud)")
        
        # Poner en cooldown si es necesario
        if account.interactions_this_hour >= self.max_per_hour:
            account.status = AccountStatus.COOLDOWN
            logger.info(f"Cuenta {account.username} en cooldown")
        
        self._update_stats()
        
        # TODO: Persistir en BD
    
    async def reset_hourly_counters(self):
        """Resetea contadores por hora."""
        for platform_accounts in self.accounts.values():
            for account in platform_accounts:
                account.interactions_this_hour = 0
                
                # Reactivar si estaba en cooldown
                if account.status == AccountStatus.COOLDOWN:
                    account.status = AccountStatus.ACTIVE
        
        logger.info("Contadores horarios reseteados")
    
    async def reset_daily_counters(self):
        """Resetea contadores diarios."""
        for platform_accounts in self.accounts.values():
            for account in platform_accounts:
                account.interactions_today = 0
        
        logger.info("Contadores diarios reseteados")
    
    async def warm_up_account(
        self,
        account: NonOfficialAccount,
        duration_days: int = 7
    ):
        """
        Warm-up de cuenta nueva.
        
        Proceso:
        - Días 1-2: Solo navegación
        - Días 3-4: 1-2 likes/día
        - Días 5-6: 3-5 likes/día
        - Día 7+: Full capacity
        
        Args:
            account: Cuenta a calentar
            duration_days: Duración del warm-up
        """
        account.status = AccountStatus.WARMING_UP
        
        logger.info(
            f"Iniciando warm-up de {account.username} "
            f"(duración: {duration_days} días)"
        )
        
        # TODO: Implementar lógica gradual de warm-up
        # Por ahora, marcar como completado después de duration
        
        await asyncio.sleep(1)  # Placeholder
        
        account.status = AccountStatus.ACTIVE
        logger.info(f"Warm-up completado: {account.username}")
    
    async def health_check_all(self):
        """Verifica salud de todas las cuentas."""
        logger.info("Ejecutando health check en todas las cuentas...")
        
        for platform, platform_accounts in self.accounts.items():
            for account in platform_accounts:
                old_health = account.health
                new_health = AccountHealthMonitor.check_health(account)
                
                if old_health != new_health:
                    account.health = new_health
                    logger.info(
                        f"Cuenta {account.username}: {old_health.value} → {new_health.value}"
                    )
                
                # Suspender si es necesario
                if AccountHealthMonitor.should_suspend(account):
                    account.status = AccountStatus.SUSPENDED
                    logger.warning(f"Cuenta {account.username} suspendida")
        
        self._update_stats()
    
    def _update_stats(self):
        """Actualiza estadísticas del pool."""
        total = 0
        active = 0
        blocked = 0
        
        for platform_accounts in self.accounts.values():
            total += len(platform_accounts)
            active += sum(1 for acc in platform_accounts if acc.status == AccountStatus.ACTIVE)
            blocked += sum(1 for acc in platform_accounts if acc.status == AccountStatus.BLOCKED)
        
        self.stats.update({
            "total_accounts": total,
            "active_accounts": active,
            "blocked_accounts": blocked
        })
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del pool."""
        return {
            **self.stats,
            "accounts_by_platform": {
                platform: len(accounts)
                for platform, accounts in self.accounts.items()
            },
            "accounts_by_health": {
                health.value: sum(
                    1 for accounts in self.accounts.values()
                    for acc in accounts if acc.health == health
                )
                for health in AccountHealth
            }
        }
