"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Account Security Layer

Capa de seguridad para cuentas satélite.
Integra proxy, fingerprint, IP isolation y detecta anomalías.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .account_models import AccountRiskLevel, AccountRiskProfile

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class SecurityLayerConfig:
    """Configuración de la capa de seguridad"""
    
    # Risk thresholds
    fingerprint_reuse_threshold: int = 3  # Max accounts per fingerprint
    ip_reuse_threshold: int = 5           # Max accounts per IP
    timing_similarity_threshold: float = 0.8
    
    # Behavioral checks
    enable_behavioral_checks: bool = True
    max_actions_per_minute: int = 5
    max_sessions_per_day: int = 20
    
    # Cooldown triggers
    shadowban_cooldown_days: int = 3
    correlation_cooldown_days: int = 2
    
    # Auto-pause triggers
    critical_risk_auto_pause: bool = True


# ============================================================================
# SECURITY CHECKS
# ============================================================================

@dataclass
class SecurityCheckResult:
    """Resultado de un security check"""
    
    passed: bool
    risk_level: AccountRiskLevel
    reason: str
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


# ============================================================================
# ACCOUNT SECURITY LAYER
# ============================================================================

class AccountSecurityLayer:
    """
    Capa de seguridad para cuentas satélite.
    
    Responsabilidades:
    - Validar proxy assignment
    - Detectar fingerprint reuse
    - Detectar IP correlation
    - Detectar patrones sospechosos de timing
    - Detectar anomalías comportamentales
    - Recomendar acciones (cooldown, pause)
    """
    
    def __init__(self, config: Optional[SecurityLayerConfig] = None):
        self.config = config or SecurityLayerConfig()
        
        # Tracking registries
        self._proxy_assignments: Dict[str, List[str]] = {}  # proxy_id -> [account_ids]
        self._fingerprint_assignments: Dict[str, List[str]] = {}  # fingerprint_id -> [account_ids]
        self._ip_assignments: Dict[str, List[str]] = {}  # ip_address -> [account_ids]
        
        # Action tracking (for rate limiting)
        self._action_timestamps: Dict[str, List[datetime]] = {}  # account_id -> [timestamps]
        
        logger.info("AccountSecurityLayer initialized")
    
    # ========================================================================
    # PUBLIC API - SECURITY CHECKS
    # ========================================================================
    
    def check_proxy_assignment(
        self,
        account_id: str,
        proxy_id: str
    ) -> SecurityCheckResult:
        """
        Valida asignación de proxy.
        
        Checks:
        - Proxy no excede límite de cuentas
        - Proxy está activo/disponible
        """
        # Get accounts using this proxy
        accounts_using_proxy = self._proxy_assignments.get(proxy_id, [])
        
        # TODO: Check with ProxyRouter if proxy is active
        
        if len(accounts_using_proxy) >= 10:  # Max 10 accounts per proxy
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.MEDIUM,
                reason="Proxy overused",
                details={"accounts_count": len(accounts_using_proxy)}
            )
        
        return SecurityCheckResult(
            passed=True,
            risk_level=AccountRiskLevel.VERY_LOW,
            reason="Proxy OK"
        )
    
    def check_fingerprint_reuse(
        self,
        account_id: str,
        fingerprint_id: str
    ) -> SecurityCheckResult:
        """
        Detecta fingerprint reuse peligroso.
        
        TikTok puede detectar si >N cuentas usan el mismo fingerprint.
        """
        accounts_using_fp = self._fingerprint_assignments.get(fingerprint_id, [])
        
        if len(accounts_using_fp) > self.config.fingerprint_reuse_threshold:
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.HIGH,
                reason=f"Fingerprint used by {len(accounts_using_fp)} accounts",
                details={
                    "fingerprint_id": fingerprint_id,
                    "accounts": accounts_using_fp[:5]  # Sample
                }
            )
        
        return SecurityCheckResult(
            passed=True,
            risk_level=AccountRiskLevel.VERY_LOW,
            reason="Fingerprint OK"
        )
    
    def check_ip_correlation(
        self,
        account_id: str,
        ip_address: str
    ) -> SecurityCheckResult:
        """
        Detecta IP correlation.
        
        Múltiples cuentas desde la misma IP es riesgoso.
        """
        accounts_using_ip = self._ip_assignments.get(ip_address, [])
        
        if len(accounts_using_ip) > self.config.ip_reuse_threshold:
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.HIGH,
                reason=f"IP used by {len(accounts_using_ip)} accounts",
                details={
                    "ip_address": ip_address,
                    "accounts": accounts_using_ip[:5]
                }
            )
        
        return SecurityCheckResult(
            passed=True,
            risk_level=AccountRiskLevel.VERY_LOW,
            reason="IP OK"
        )
    
    def check_timing_patterns(
        self,
        account_id: str,
        action_timestamps: List[datetime]
    ) -> SecurityCheckResult:
        """
        Detecta patrones sospechosos de timing.
        
        Acciones con intervalos demasiado regulares = bot detection.
        """
        if len(action_timestamps) < 5:
            return SecurityCheckResult(
                passed=True,
                risk_level=AccountRiskLevel.VERY_LOW,
                reason="Not enough data"
            )
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(action_timestamps)):
            delta = (action_timestamps[i] - action_timestamps[i-1]).total_seconds()
            intervals.append(delta)
        
        # Calculate variance
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = std_dev / mean_interval if mean_interval > 0 else 0
        
        # Low CV = too regular = suspicious
        if cv < 0.3:  # Less than 30% variation
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.MEDIUM,
                reason="Timing too regular (bot-like)",
                details={
                    "mean_interval": mean_interval,
                    "cv": cv
                }
            )
        
        return SecurityCheckResult(
            passed=True,
            risk_level=AccountRiskLevel.VERY_LOW,
            reason="Timing patterns OK"
        )
    
    def check_behavioral_anomalies(
        self,
        account_id: str
    ) -> SecurityCheckResult:
        """
        Detecta anomalías comportamentales.
        
        Checks:
        - Rate limiting (acciones por minuto)
        - Session frequency
        - Action bursts
        """
        if not self.config.enable_behavioral_checks:
            return SecurityCheckResult(
                passed=True,
                risk_level=AccountRiskLevel.VERY_LOW,
                reason="Behavioral checks disabled"
            )
        
        # Get recent actions
        timestamps = self._action_timestamps.get(account_id, [])
        if not timestamps:
            return SecurityCheckResult(
                passed=True,
                risk_level=AccountRiskLevel.VERY_LOW,
                reason="No actions yet"
            )
        
        now = datetime.now()
        
        # Check rate limiting (last minute)
        one_minute_ago = now - timedelta(minutes=1)
        actions_last_minute = [ts for ts in timestamps if ts >= one_minute_ago]
        
        if len(actions_last_minute) > self.config.max_actions_per_minute:
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.HIGH,
                reason=f"Too many actions in last minute: {len(actions_last_minute)}",
                details={"actions_per_minute": len(actions_last_minute)}
            )
        
        # Check session frequency (today)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        actions_today = [ts for ts in timestamps if ts >= today_start]
        
        # Estimate sessions (gap > 10min = new session)
        sessions = 1
        for i in range(1, len(actions_today)):
            gap = (actions_today[i] - actions_today[i-1]).total_seconds()
            if gap > 600:  # 10 minutes
                sessions += 1
        
        if sessions > self.config.max_sessions_per_day:
            return SecurityCheckResult(
                passed=False,
                risk_level=AccountRiskLevel.MEDIUM,
                reason=f"Too many sessions today: {sessions}",
                details={"sessions_today": sessions}
            )
        
        return SecurityCheckResult(
            passed=True,
            risk_level=AccountRiskLevel.VERY_LOW,
            reason="Behavioral checks passed"
        )
    
    def run_full_security_check(
        self,
        account_id: str,
        proxy_id: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, AccountRiskLevel, List[str]]:
        """
        Ejecuta todos los security checks.
        
        Returns:
            (all_passed, highest_risk_level, reasons)
        """
        results = []
        reasons = []
        
        # Check proxy
        if proxy_id:
            result = self.check_proxy_assignment(account_id, proxy_id)
            results.append(result)
            if not result.passed:
                reasons.append(result.reason)
        
        # Check fingerprint
        if fingerprint_id:
            result = self.check_fingerprint_reuse(account_id, fingerprint_id)
            results.append(result)
            if not result.passed:
                reasons.append(result.reason)
        
        # Check IP
        if ip_address:
            result = self.check_ip_correlation(account_id, ip_address)
            results.append(result)
            if not result.passed:
                reasons.append(result.reason)
        
        # Check timing
        timestamps = self._action_timestamps.get(account_id, [])
        if timestamps:
            result = self.check_timing_patterns(account_id, timestamps)
            results.append(result)
            if not result.passed:
                reasons.append(result.reason)
        
        # Check behavioral
        result = self.check_behavioral_anomalies(account_id)
        results.append(result)
        if not result.passed:
            reasons.append(result.reason)
        
        # Aggregate results
        all_passed = all(r.passed for r in results)
        
        # Get highest risk level
        risk_levels = [r.risk_level for r in results]
        risk_order = [
            AccountRiskLevel.VERY_LOW,
            AccountRiskLevel.LOW,
            AccountRiskLevel.MEDIUM,
            AccountRiskLevel.HIGH,
            AccountRiskLevel.CRITICAL
        ]
        highest_risk = max(risk_levels, key=lambda r: risk_order.index(r))
        
        return all_passed, highest_risk, reasons
    
    # ========================================================================
    # PUBLIC API - REGISTRATION
    # ========================================================================
    
    def register_proxy(self, account_id: str, proxy_id: str):
        """Registra asignación de proxy"""
        if proxy_id not in self._proxy_assignments:
            self._proxy_assignments[proxy_id] = []
        
        if account_id not in self._proxy_assignments[proxy_id]:
            self._proxy_assignments[proxy_id].append(account_id)
    
    def register_fingerprint(self, account_id: str, fingerprint_id: str):
        """Registra asignación de fingerprint"""
        if fingerprint_id not in self._fingerprint_assignments:
            self._fingerprint_assignments[fingerprint_id] = []
        
        if account_id not in self._fingerprint_assignments[fingerprint_id]:
            self._fingerprint_assignments[fingerprint_id].append(account_id)
    
    def register_ip(self, account_id: str, ip_address: str):
        """Registra uso de IP"""
        if ip_address not in self._ip_assignments:
            self._ip_assignments[ip_address] = []
        
        if account_id not in self._ip_assignments[ip_address]:
            self._ip_assignments[ip_address].append(account_id)
    
    def record_action(self, account_id: str, timestamp: Optional[datetime] = None):
        """Registra una acción (para timing analysis)"""
        if account_id not in self._action_timestamps:
            self._action_timestamps[account_id] = []
        
        ts = timestamp or datetime.now()
        self._action_timestamps[account_id].append(ts)
        
        # Keep only last 1000 actions
        if len(self._action_timestamps[account_id]) > 1000:
            self._action_timestamps[account_id] = self._action_timestamps[account_id][-1000:]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_security_layer() -> AccountSecurityLayer:
    """Helper para crear security layer"""
    return AccountSecurityLayer()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SecurityLayerConfig",
    "SecurityCheckResult",
    "AccountSecurityLayer",
    "create_security_layer",
]
