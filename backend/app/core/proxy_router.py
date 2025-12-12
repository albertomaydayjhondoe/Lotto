"""
🔐 PROXY ROUTER - Sistema central de enrutamiento de proxies

Este módulo implementa el router que asigna automáticamente proxies
según el tipo de componente, garantizando aislamiento total.

POLÍTICA DE AISLAMIENTO:
- Cada cuenta satélite: proxy único
- TelegramBot: VPN exclusiva
- Scrapers: pool rotativo
- APIs oficiales: backend IP (permitido)

Autor: STAKAZO Security Team
Fecha: Diciembre 2025
Versión: 1.0.0
"""

import os
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime
import random
import asyncio
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Tipos de componentes del sistema"""
    SATELLITE_ACCOUNT = "satellite_account"
    TELEGRAM_BOT = "telegram_bot"
    SCRAPER = "scraper"
    OFFICIAL_API = "official_api"
    ORCHESTRATOR = "orchestrator"


class ProxyType(str, Enum):
    """Tipos de proxies disponibles"""
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    VPN = "vpn"


class ProxyConfig(BaseModel):
    """Configuración de un proxy"""
    proxy_id: str
    proxy_type: ProxyType
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    country: Optional[str] = None
    city: Optional[str] = None
    is_available: bool = True
    last_used: Optional[datetime] = None
    assigned_to: Optional[str] = None  # component_id
    success_rate: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0


class ProxyAssignment(BaseModel):
    """Asignación de proxy a componente"""
    component_id: str
    component_type: ComponentType
    proxy_config: ProxyConfig
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class ProxyRouter:
    """
    Router central de proxies
    
    Garantiza que cada componente use el proxy correcto:
    - Satélites: proxy único asignado
    - TelegramBot: VPN exclusiva
    - Scrapers: rotación de pool
    - APIs oficiales: backend IP
    """
    
    def __init__(self):
        self.satellite_proxies: Dict[str, ProxyConfig] = {}
        self.telegram_bot_proxy: Optional[ProxyConfig] = None
        self.scraper_proxy_pool: List[ProxyConfig] = []
        self.assignments: Dict[str, ProxyAssignment] = {}
        
        # Stats
        self.total_assignments = 0
        self.blocked_attempts = 0
        
        # Load from config
        self._load_proxy_configs()
    
    def _load_proxy_configs(self):
        """Carga configuraciones de proxies desde variables de entorno"""
        # TODO: En producción, cargar desde base de datos o archivo config
        
        # Ejemplo: SATELLITE_PROXY_1=residential:host:port:user:pass:US
        # Ejemplo: TELEGRAM_BOT_PROXY=vpn:host:port:user:pass:ES
        # Ejemplo: SCRAPER_PROXY_POOL=mobile:host1:port1:user:pass:US,mobile:host2:port2:user:pass:UK
        
        # Por ahora, proxies de ejemplo (DEMO)
        self._init_demo_proxies()
    
    def _init_demo_proxies(self):
        """Inicializa proxies de demostración"""
        # Proxy para TelegramBot (VPN exclusiva)
        self.telegram_bot_proxy = ProxyConfig(
            proxy_id="telegram_bot_vpn_001",
            proxy_type=ProxyType.VPN,
            host="telegram-vpn.example.com",
            port=8080,
            username="telegram_bot",
            password="secure_pass",
            country="ES",
            assigned_to="telegram_exchange_engine"
        )
        
        # Pool de proxies para scrapers (rotativos)
        for i in range(5):
            self.scraper_proxy_pool.append(
                ProxyConfig(
                    proxy_id=f"scraper_mobile_{i+1:03d}",
                    proxy_type=ProxyType.MOBILE,
                    host=f"scraper-pool-{i+1}.example.com",
                    port=8080,
                    username=f"scraper_{i+1}",
                    password="secure_pass",
                    country=random.choice(["US", "UK", "CA", "AU", "DE"])
                )
            )
    
    def assign_proxy(
        self,
        component_id: str,
        component_type: ComponentType,
        force_new: bool = False
    ) -> Optional[ProxyConfig]:
        """
        Asigna un proxy al componente según su tipo
        
        Args:
            component_id: ID único del componente
            component_type: Tipo de componente
            force_new: Forzar asignación de nuevo proxy
        
        Returns:
            ProxyConfig asignado o None si no requiere proxy
        """
        
        # Verificar si ya tiene asignación activa
        if not force_new and component_id in self.assignments:
            assignment = self.assignments[component_id]
            if assignment.is_active:
                return assignment.proxy_config
        
        # Asignar según tipo
        if component_type == ComponentType.SATELLITE_ACCOUNT:
            return self._assign_satellite_proxy(component_id)
        
        elif component_type == ComponentType.TELEGRAM_BOT:
            return self._assign_telegram_bot_proxy(component_id)
        
        elif component_type == ComponentType.SCRAPER:
            return self._assign_scraper_proxy(component_id)
        
        elif component_type in [ComponentType.OFFICIAL_API, ComponentType.ORCHESTRATOR]:
            # No requiere proxy (usa backend IP)
            return None
        
        return None
    
    def _assign_satellite_proxy(self, satellite_id: str) -> ProxyConfig:
        """
        Asigna proxy único a cuenta satélite
        
        CRÍTICO: Cada satélite debe tener SU PROPIO proxy
        """
        
        # Verificar si ya tiene proxy asignado
        if satellite_id in self.satellite_proxies:
            proxy = self.satellite_proxies[satellite_id]
            if proxy.is_available:
                return proxy
        
        # Crear nuevo proxy único para este satélite
        # TODO: En producción, obtener de pool de proxies residenciales
        proxy = ProxyConfig(
            proxy_id=f"satellite_{satellite_id}_proxy",
            proxy_type=ProxyType.RESIDENTIAL,
            host=f"satellite-{satellite_id}.proxy-pool.example.com",
            port=8080,
            username=f"satellite_{satellite_id}",
            password="secure_pass",
            country=random.choice(["US", "UK", "CA", "AU", "ES", "MX"]),
            assigned_to=satellite_id
        )
        
        # Guardar asignación
        self.satellite_proxies[satellite_id] = proxy
        self.assignments[satellite_id] = ProxyAssignment(
            component_id=satellite_id,
            component_type=ComponentType.SATELLITE_ACCOUNT,
            proxy_config=proxy
        )
        
        self.total_assignments += 1
        
        return proxy
    
    def _assign_telegram_bot_proxy(self, bot_id: str) -> ProxyConfig:
        """
        Asigna VPN exclusiva al TelegramBot
        
        CRÍTICO: El bot NUNCA puede compartir IP con satélites o backend
        """
        
        if self.telegram_bot_proxy is None:
            raise ValueError("TelegramBot VPN no configurada. Ver POLITICA_AISLAMIENTO_IDENTIDAD.md")
        
        # Asignar VPN exclusiva
        self.assignments[bot_id] = ProxyAssignment(
            component_id=bot_id,
            component_type=ComponentType.TELEGRAM_BOT,
            proxy_config=self.telegram_bot_proxy
        )
        
        self.total_assignments += 1
        
        return self.telegram_bot_proxy
    
    def _assign_scraper_proxy(self, scraper_id: str) -> ProxyConfig:
        """
        Asigna proxy rotativo del pool de scrapers
        
        Los scrapers rotan entre un pool dedicado
        """
        
        if not self.scraper_proxy_pool:
            raise ValueError("Scraper proxy pool vacío. Configurar proxies para scrapers.")
        
        # Seleccionar proxy con menor uso reciente
        available_proxies = [
            p for p in self.scraper_proxy_pool
            if p.is_available and p.success_rate > 0.7
        ]
        
        if not available_proxies:
            # Todos están en uso o tienen baja tasa de éxito
            available_proxies = self.scraper_proxy_pool
        
        # Ordenar por último uso
        available_proxies.sort(
            key=lambda p: p.last_used if p.last_used else datetime.min
        )
        
        # Tomar el menos usado recientemente
        proxy = available_proxies[0]
        proxy.last_used = datetime.utcnow()
        
        # Asignar
        self.assignments[scraper_id] = ProxyAssignment(
            component_id=scraper_id,
            component_type=ComponentType.SCRAPER,
            proxy_config=proxy
        )
        
        self.total_assignments += 1
        
        return proxy
    
    def get_proxy_url(self, component_id: str) -> Optional[str]:
        """
        Obtiene URL del proxy asignado
        
        Returns:
            URL completa del proxy o None si no requiere
        """
        
        if component_id not in self.assignments:
            return None
        
        assignment = self.assignments[component_id]
        if not assignment.is_active:
            return None
        
        proxy = assignment.proxy_config
        
        # Construir URL
        if proxy.username and proxy.password:
            auth = f"{proxy.username}:{proxy.password}@"
        else:
            auth = ""
        
        return f"{proxy.protocol}://{auth}{proxy.host}:{proxy.port}"
    
    def validate_request(self, component_id: str, component_type: ComponentType) -> bool:
        """
        Valida que la request use el proxy correcto
        
        CRÍTICO: Bloquea requests que violen política de aislamiento
        """
        
        # Componentes que NO deben usar proxy
        if component_type in [ComponentType.OFFICIAL_API, ComponentType.ORCHESTRATOR]:
            # Verificar que NO estén usando proxy
            if component_id in self.assignments:
                self.blocked_attempts += 1
                return False
            return True
        
        # Componentes que SÍ deben usar proxy
        if component_type in [ComponentType.SATELLITE_ACCOUNT, ComponentType.TELEGRAM_BOT, ComponentType.SCRAPER]:
            # Verificar que SÍ tengan proxy asignado
            if component_id not in self.assignments:
                self.blocked_attempts += 1
                return False
            
            assignment = self.assignments[component_id]
            if not assignment.is_active:
                self.blocked_attempts += 1
                return False
            
            return True
        
        return False
    
    def report_proxy_status(self, component_id: str, success: bool):
        """Reporta resultado de uso del proxy (para estadísticas)"""
        
        if component_id not in self.assignments:
            return
        
        assignment = self.assignments[component_id]
        proxy = assignment.proxy_config
        
        proxy.total_requests += 1
        
        if not success:
            proxy.failed_requests += 1
        
        # Recalcular tasa de éxito
        if proxy.total_requests > 0:
            proxy.success_rate = 1.0 - (proxy.failed_requests / proxy.total_requests)
        
        # Marcar como no disponible si tasa de éxito < 50%
        if proxy.success_rate < 0.5:
            proxy.is_available = False
    
    def release_proxy(self, component_id: str):
        """Libera proxy asignado a componente"""
        
        if component_id in self.assignments:
            assignment = self.assignments[component_id]
            assignment.is_active = False
            
            # Si es de satellite, mantener reservado
            # Si es de scraper, liberar para rotación
            if assignment.component_type == ComponentType.SCRAPER:
                assignment.proxy_config.assigned_to = None
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del router"""
        
        return {
            "total_assignments": self.total_assignments,
            "blocked_attempts": self.blocked_attempts,
            "active_satellites": len([
                a for a in self.assignments.values()
                if a.component_type == ComponentType.SATELLITE_ACCOUNT and a.is_active
            ]),
            "telegram_bot_active": any(
                a.component_type == ComponentType.TELEGRAM_BOT and a.is_active
                for a in self.assignments.values()
            ),
            "scraper_pool_size": len(self.scraper_proxy_pool),
            "scraper_pool_available": len([
                p for p in self.scraper_proxy_pool
                if p.is_available and p.success_rate > 0.7
            ])
        }
    
    def validate_isolation_policy(self) -> Dict[str, bool]:
        """
        Valida que se cumpla la política de aislamiento
        
        Returns:
            Dict con validaciones por regla
        """
        
        validations = {
            "no_shared_ips_satellites": True,
            "telegram_bot_isolated": True,
            "scrapers_separate_pool": True,
            "official_apis_no_proxy": True
        }
        
        # Verificar que no hay IPs compartidas entre satélites
        satellite_ips = []
        for assignment in self.assignments.values():
            if assignment.component_type == ComponentType.SATELLITE_ACCOUNT:
                ip = assignment.proxy_config.host
                if ip in satellite_ips:
                    validations["no_shared_ips_satellites"] = False
                satellite_ips.append(ip)
        
        # Verificar que TelegramBot tiene VPN exclusiva
        telegram_assignments = [
            a for a in self.assignments.values()
            if a.component_type == ComponentType.TELEGRAM_BOT
        ]
        if telegram_assignments:
            telegram_ip = telegram_assignments[0].proxy_config.host
            if telegram_ip in satellite_ips:
                validations["telegram_bot_isolated"] = False
        
        # Verificar que scrapers usan pool separado
        scraper_assignments = [
            a for a in self.assignments.values()
            if a.component_type == ComponentType.SCRAPER
        ]
        for assignment in scraper_assignments:
            scraper_ip = assignment.proxy_config.host
            if scraper_ip in satellite_ips or (telegram_assignments and scraper_ip == telegram_ip):
                validations["scrapers_separate_pool"] = False
        
        return validations


# Singleton global
_proxy_router_instance = None


def get_proxy_router() -> ProxyRouter:
    """Obtiene instancia singleton del ProxyRouter"""
    global _proxy_router_instance
    if _proxy_router_instance is None:
        _proxy_router_instance = ProxyRouter()
    return _proxy_router_instance
