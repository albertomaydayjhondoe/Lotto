"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Universe Profile Manager

Gestor de perfiles del universo de cuentas satélite:
- 1 cuenta → 1 nicho (identity enforcement)
- State tracking (active, warmup, suspended)
- Performance metrics & history
- Optimal timing learning
"""

import logging
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .sat_intel_contracts import AccountProfile

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class ProfileManagerConfig:
    """Configuración del profile manager"""
    
    # Warmup settings
    warmup_duration_days: int = 14
    warmup_posts_per_day: int = 2
    
    # Activity thresholds
    inactive_threshold_days: int = 7
    shadowban_signal_threshold: int = 3
    correlation_signal_threshold: int = 2
    
    # History limits
    recent_content_window_days: int = 30
    max_recent_items: int = 100


# ============================================================================
# UNIVERSE PROFILE MANAGER
# ============================================================================

class UniverseProfileManager:
    """
    Gestor centralizado de perfiles de cuentas satélite.
    
    Responsabilidades:
    - CRUD de profiles
    - State management (warmup, active, suspended)
    - Performance tracking
    - History management
    - Niche enforcement (1 cuenta → 1 nicho)
    """
    
    def __init__(self, config: Optional[ProfileManagerConfig] = None):
        self.config = config or ProfileManagerConfig()
        self._profiles: Dict[str, AccountProfile] = {}
        self._niche_allocations: Dict[str, List[str]] = {}  # niche_id → [account_ids]
        
        logger.info("UniverseProfileManager initialized")
    
    # ========================================================================
    # PROFILE CRUD
    # ========================================================================
    
    def create_profile(
        self,
        account_id: str,
        niche_id: str,
        niche_name: str,
        start_warmup: bool = True
    ) -> AccountProfile:
        """
        Crea un nuevo profile para una cuenta.
        
        Args:
            account_id: ID único de la cuenta
            niche_id: ID del nicho asignado
            niche_name: Nombre del nicho
            start_warmup: Si True, inicia en modo warmup
        
        Returns:
            AccountProfile creado
        """
        if account_id in self._profiles:
            raise ValueError(f"Profile {account_id} already exists")
        
        # Enforce 1 cuenta → 1 nicho
        if niche_id not in self._niche_allocations:
            self._niche_allocations[niche_id] = []
        
        profile = AccountProfile(
            account_id=account_id,
            niche_id=niche_id,
            niche_name=niche_name,
            is_active=start_warmup,
            warmup_completed=False,
            warmup_day=1 if start_warmup else 0,
            total_posts=0,
            last_post_at=None,
            avg_retention=0.0,
            avg_engagement=0.0,
            recent_content_ids=[],
            recent_audio_ids=[],
            optimal_hours=[],
            optimal_days=[],
            shadowban_signals=0,
            correlation_signals=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        self._profiles[account_id] = profile
        self._niche_allocations[niche_id].append(account_id)
        
        logger.info(f"Created profile {account_id} for niche '{niche_name}' (warmup={start_warmup})")
        return profile
    
    def get_profile(self, account_id: str) -> Optional[AccountProfile]:
        """Get profile por account_id"""
        return self._profiles.get(account_id)
    
    def update_profile(self, account_id: str, **updates) -> AccountProfile:
        """
        Update profile con campos específicos.
        
        Example:
            manager.update_profile("acc_123", is_active=False, avg_retention=0.85)
        """
        if account_id not in self._profiles:
            raise ValueError(f"Profile {account_id} not found")
        
        profile = self._profiles[account_id]
        updated_profile = replace(profile, updated_at=datetime.now(), **updates)
        self._profiles[account_id] = updated_profile
        
        logger.debug(f"Updated profile {account_id}: {list(updates.keys())}")
        return updated_profile
    
    def delete_profile(self, account_id: str) -> None:
        """Elimina un profile"""
        if account_id not in self._profiles:
            raise ValueError(f"Profile {account_id} not found")
        
        profile = self._profiles[account_id]
        
        # Remove from niche allocations
        if profile.niche_id in self._niche_allocations:
            self._niche_allocations[profile.niche_id].remove(account_id)
        
        del self._profiles[account_id]
        logger.info(f"Deleted profile {account_id}")
    
    # ========================================================================
    # QUERYING
    # ========================================================================
    
    def list_profiles(
        self,
        niche_id: Optional[str] = None,
        active_only: bool = False,
        warmup_only: bool = False
    ) -> List[AccountProfile]:
        """
        Lista profiles con filtros opcionales.
        
        Args:
            niche_id: Filtrar por nicho
            active_only: Solo cuentas activas
            warmup_only: Solo cuentas en warmup
        """
        profiles = list(self._profiles.values())
        
        if niche_id:
            profiles = [p for p in profiles if p.niche_id == niche_id]
        
        if active_only:
            profiles = [p for p in profiles if p.is_active]
        
        if warmup_only:
            profiles = [p for p in profiles if not p.warmup_completed]
        
        return profiles
    
    def get_niche_accounts(self, niche_id: str) -> List[AccountProfile]:
        """Get todas las cuentas de un nicho"""
        account_ids = self._niche_allocations.get(niche_id, [])
        return [self._profiles[aid] for aid in account_ids if aid in self._profiles]
    
    def get_active_accounts(self) -> List[AccountProfile]:
        """Get todas las cuentas activas"""
        return self.list_profiles(active_only=True)
    
    def get_warmup_accounts(self) -> List[AccountProfile]:
        """Get todas las cuentas en warmup"""
        return self.list_profiles(warmup_only=True)
    
    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================
    
    def advance_warmup(self, account_id: str) -> AccountProfile:
        """
        Avanza el warmup de una cuenta en 1 día.
        
        Si llega a warmup_duration_days → marca como completado.
        """
        profile = self.get_profile(account_id)
        if not profile:
            raise ValueError(f"Profile {account_id} not found")
        
        if profile.warmup_completed:
            logger.warning(f"Profile {account_id} already completed warmup")
            return profile
        
        new_day = profile.warmup_day + 1
        
        if new_day >= self.config.warmup_duration_days:
            # Warmup complete
            logger.info(f"Profile {account_id} completed warmup (day {new_day})")
            return self.update_profile(
                account_id,
                warmup_day=new_day,
                warmup_completed=True
            )
        else:
            return self.update_profile(account_id, warmup_day=new_day)
    
    def suspend_account(self, account_id: str, reason: str = "") -> AccountProfile:
        """Suspende una cuenta (marca is_active=False)"""
        logger.warning(f"Suspending account {account_id}: {reason}")
        return self.update_profile(account_id, is_active=False)
    
    def activate_account(self, account_id: str) -> AccountProfile:
        """Activa una cuenta suspendida"""
        logger.info(f"Activating account {account_id}")
        return self.update_profile(account_id, is_active=True)
    
    # ========================================================================
    # PERFORMANCE TRACKING
    # ========================================================================
    
    def record_post(
        self,
        account_id: str,
        content_id: str,
        audio_id: Optional[str] = None,
        retention: Optional[float] = None,
        engagement: Optional[float] = None
    ) -> AccountProfile:
        """
        Registra un post exitoso para una cuenta.
        
        Actualiza:
        - total_posts
        - last_post_at
        - recent_content_ids / recent_audio_ids
        - avg_retention / avg_engagement (si se proveen)
        """
        profile = self.get_profile(account_id)
        if not profile:
            raise ValueError(f"Profile {account_id} not found")
        
        # Update counts & timestamps
        new_total = profile.total_posts + 1
        now = datetime.now()
        
        # Update recent lists
        new_content_ids = profile.recent_content_ids + [content_id]
        new_content_ids = new_content_ids[-self.config.max_recent_items:]
        
        new_audio_ids = profile.recent_audio_ids
        if audio_id:
            new_audio_ids = new_audio_ids + [audio_id]
            new_audio_ids = new_audio_ids[-self.config.max_recent_items:]
        
        # Update averages (weighted)
        updates = {
            "total_posts": new_total,
            "last_post_at": now,
            "recent_content_ids": new_content_ids,
            "recent_audio_ids": new_audio_ids,
        }
        
        if retention is not None:
            # Exponential moving average
            alpha = 0.3
            new_avg_retention = alpha * retention + (1 - alpha) * profile.avg_retention
            updates["avg_retention"] = new_avg_retention
        
        if engagement is not None:
            alpha = 0.3
            new_avg_engagement = alpha * engagement + (1 - alpha) * profile.avg_engagement
            updates["avg_engagement"] = new_avg_engagement
        
        updated_profile = self.update_profile(account_id, **updates)
        
        logger.debug(f"Recorded post for {account_id}: content={content_id}, "
                    f"total_posts={new_total}, retention={retention}, engagement={engagement}")
        
        return updated_profile
    
    def update_optimal_timing(
        self,
        account_id: str,
        optimal_hours: List[int],
        optimal_days: List[int]
    ) -> AccountProfile:
        """Update optimal timing basado en ML learning"""
        logger.info(f"Updated optimal timing for {account_id}: hours={optimal_hours}, days={optimal_days}")
        return self.update_profile(
            account_id,
            optimal_hours=optimal_hours,
            optimal_days=optimal_days
        )
    
    def flag_shadowban_signal(self, account_id: str) -> AccountProfile:
        """Incrementa contador de shadowban signals"""
        profile = self.get_profile(account_id)
        if not profile:
            raise ValueError(f"Profile {account_id} not found")
        
        new_signals = profile.shadowban_signals + 1
        
        logger.warning(f"Shadowban signal for {account_id} (total={new_signals})")
        
        # Auto-suspend si excede threshold
        if new_signals >= self.config.shadowban_signal_threshold:
            logger.error(f"Account {account_id} exceeded shadowban threshold, suspending")
            return self.update_profile(
                account_id,
                shadowban_signals=new_signals,
                is_active=False
            )
        
        return self.update_profile(account_id, shadowban_signals=new_signals)
    
    def flag_correlation_signal(self, account_id: str) -> AccountProfile:
        """Incrementa contador de correlation signals"""
        profile = self.get_profile(account_id)
        if not profile:
            raise ValueError(f"Profile {account_id} not found")
        
        new_signals = profile.correlation_signals + 1
        
        logger.warning(f"Correlation signal for {account_id} (total={new_signals})")
        
        # Auto-suspend si excede threshold
        if new_signals >= self.config.correlation_signal_threshold:
            logger.error(f"Account {account_id} exceeded correlation threshold, suspending")
            return self.update_profile(
                account_id,
                correlation_signals=new_signals,
                is_active=False
            )
        
        return self.update_profile(account_id, correlation_signals=new_signals)
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_universe_stats(self) -> Dict:
        """Retorna estadísticas del universo completo"""
        profiles = list(self._profiles.values())
        
        if not profiles:
            return {
                "total_accounts": 0,
                "active_accounts": 0,
                "warmup_accounts": 0,
                "suspended_accounts": 0,
                "total_posts": 0,
                "avg_retention": 0.0,
                "avg_engagement": 0.0,
                "niches": 0,
            }
        
        active = [p for p in profiles if p.is_active]
        warmup = [p for p in profiles if not p.warmup_completed]
        suspended = [p for p in profiles if not p.is_active]
        
        total_posts = sum(p.total_posts for p in profiles)
        
        # Weighted averages
        total_weighted_retention = sum(p.avg_retention * p.total_posts for p in profiles)
        total_weighted_engagement = sum(p.avg_engagement * p.total_posts for p in profiles)
        
        avg_retention = total_weighted_retention / total_posts if total_posts > 0 else 0.0
        avg_engagement = total_weighted_engagement / total_posts if total_posts > 0 else 0.0
        
        return {
            "total_accounts": len(profiles),
            "active_accounts": len(active),
            "warmup_accounts": len(warmup),
            "suspended_accounts": len(suspended),
            "total_posts": total_posts,
            "avg_retention": avg_retention,
            "avg_engagement": avg_engagement,
            "niches": len(self._niche_allocations),
        }
    
    def get_niche_stats(self, niche_id: str) -> Dict:
        """Retorna estadísticas de un nicho específico"""
        accounts = self.get_niche_accounts(niche_id)
        
        if not accounts:
            return {
                "niche_id": niche_id,
                "total_accounts": 0,
                "active_accounts": 0,
                "total_posts": 0,
                "avg_retention": 0.0,
                "avg_engagement": 0.0,
            }
        
        active = [a for a in accounts if a.is_active]
        total_posts = sum(a.total_posts for a in accounts)
        
        # Weighted averages
        total_weighted_retention = sum(a.avg_retention * a.total_posts for a in accounts)
        total_weighted_engagement = sum(a.avg_engagement * a.total_posts for a in accounts)
        
        avg_retention = total_weighted_retention / total_posts if total_posts > 0 else 0.0
        avg_engagement = total_weighted_engagement / total_posts if total_posts > 0 else 0.0
        
        return {
            "niche_id": niche_id,
            "total_accounts": len(accounts),
            "active_accounts": len(active),
            "total_posts": total_posts,
            "avg_retention": avg_retention,
            "avg_engagement": avg_engagement,
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ProfileManagerConfig",
    "UniverseProfileManager",
]
