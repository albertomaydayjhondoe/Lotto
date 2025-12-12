"""
SPRINT 12 - Account BirthFlow & Lifecycle Management
Module: Account Metrics Collector

Colector de métricas para cuentas satélite.
Calcula maturity_score, risk_score, readiness_level.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from .account_models import (
    Account,
    AccountWarmupMetrics,
    AccountRiskProfile,
    AccountState,
    is_warmup_state,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class MetricsCollectorConfig:
    """Configuración del colector de métricas"""
    
    # Maturity scoring weights
    maturity_weight_actions: float = 0.3
    maturity_weight_engagement: float = 0.3
    maturity_weight_quality: float = 0.2
    maturity_weight_consistency: float = 0.2
    
    # Risk scoring weights (must match account_models.py)
    risk_weight_shadowban: float = 0.3
    risk_weight_correlation: float = 0.3
    risk_weight_fingerprint: float = 0.15
    risk_weight_behavioral: float = 0.15
    risk_weight_timing: float = 0.10
    
    # Readiness thresholds
    min_maturity_for_secured: float = 0.6
    min_maturity_for_active: float = 0.7
    min_maturity_for_scaling: float = 0.8
    
    # Quality thresholds
    max_block_ratio: float = 0.05  # 5% max blocks
    min_engagement_ratio: float = 0.02  # 2% min engagement


# ============================================================================
# ACCOUNT METRICS COLLECTOR
# ============================================================================

class AccountMetricsCollector:
    """
    Colector de métricas para cuentas.
    
    Responsabilidades:
    - Calcular maturity_score (0-1)
    - Calcular risk_score (0-1)
    - Calcular readiness_level (0-1)
    - Trackear engagement recibido
    - Detectar señales de shadowban
    """
    
    def __init__(self, config: Optional[MetricsCollectorConfig] = None):
        self.config = config or MetricsCollectorConfig()
        
        logger.info("AccountMetricsCollector initialized")
    
    # ========================================================================
    # PUBLIC API - METRIC CALCULATION
    # ========================================================================
    
    def calculate_maturity_score(
        self,
        account: Account,
        metrics: AccountWarmupMetrics
    ) -> float:
        """
        Calcula el maturity score de una cuenta.
        
        Componentes:
        - Actions performed (30%)
        - Engagement received (30%)
        - Quality metrics (20%)
        - Consistency (20%)
        
        Returns:
            Score 0.0-1.0
        """
        # Component 1: Actions performed
        total_actions = (
            metrics.views_performed +
            metrics.likes_performed +
            metrics.comments_performed +
            metrics.follows_performed +
            metrics.posts_performed
        )
        
        # Expected actions by day
        expected_by_day = {
            1: 20, 2: 20, 3: 20,  # W1_3
            4: 40, 5: 40, 6: 40, 7: 40,  # W4_7
            8: 60, 9: 60, 10: 60, 11: 60, 12: 60, 13: 60, 14: 60  # W8_14
        }
        expected = expected_by_day.get(metrics.warmup_day, 100)
        
        actions_score = min(1.0, total_actions / expected) if expected > 0 else 0.0
        
        # Component 2: Engagement received
        total_engagement = (
            metrics.likes_received +
            metrics.comments_received +
            metrics.follows_received +
            metrics.shares_received
        )
        
        # Expected engagement (assume 2% of impressions)
        expected_engagement = metrics.impressions_received * 0.02
        engagement_score = min(1.0, total_engagement / expected_engagement) if expected_engagement > 0 else 0.0
        
        # Component 3: Quality metrics
        quality_score = self._calculate_quality_score(metrics)
        
        # Component 4: Consistency (days active / days expected)
        days_since_created = (datetime.now() - account.created_at).days
        expected_days = metrics.warmup_day if metrics.warmup_day > 0 else 1
        consistency_score = min(1.0, days_since_created / expected_days) if expected_days > 0 else 0.0
        
        # Weighted average
        maturity = (
            actions_score * self.config.maturity_weight_actions +
            engagement_score * self.config.maturity_weight_engagement +
            quality_score * self.config.maturity_weight_quality +
            consistency_score * self.config.maturity_weight_consistency
        )
        
        return round(maturity, 3)
    
    def calculate_risk_score(
        self,
        risk_profile: AccountRiskProfile
    ) -> float:
        """
        Calcula el risk score agregado.
        
        Ya implementado en account_models.calculate_total_risk()
        """
        from .account_models import calculate_total_risk
        
        return calculate_total_risk(risk_profile)
    
    def calculate_readiness_level(
        self,
        account: Account,
        metrics: AccountWarmupMetrics,
        risk_profile: AccountRiskProfile
    ) -> float:
        """
        Calcula el readiness level para avanzar de estado.
        
        Combina maturity_score y risk_score.
        
        Returns:
            Readiness 0.0-1.0
        """
        maturity = self.calculate_maturity_score(account, metrics)
        risk = self.calculate_risk_score(risk_profile)
        
        # Readiness = maturity * (1 - risk)
        # High maturity + low risk = high readiness
        readiness = maturity * (1.0 - risk)
        
        return round(readiness, 3)
    
    def update_metrics(
        self,
        account: Account,
        metrics: AccountWarmupMetrics,
        risk_profile: AccountRiskProfile
    ):
        """
        Actualiza todos los scores calculados en los modelos.
        """
        # Update maturity
        metrics.maturity_score = self.calculate_maturity_score(account, metrics)
        
        # Update risk
        risk_profile.total_risk_score = self.calculate_risk_score(risk_profile)
        
        # Update readiness
        metrics.readiness_level = self.calculate_readiness_level(account, metrics, risk_profile)
        
        # Update risk level
        from .account_models import determine_risk_level
        risk_profile.risk_level = determine_risk_level(risk_profile.total_risk_score)
        
        logger.debug(f"Updated metrics for {account.account_id}: maturity={metrics.maturity_score:.2f}, risk={risk_profile.total_risk_score:.2f}, readiness={metrics.readiness_level:.2f}")
    
    # ========================================================================
    # PUBLIC API - SIGNAL DETECTION
    # ========================================================================
    
    def detect_shadowban_signals(
        self,
        metrics: AccountWarmupMetrics
    ) -> tuple[bool, float]:
        """
        Detecta señales de shadowban.
        
        Señales:
        - Impressions drástico drop
        - Engagement rate muy bajo
        - 0 views por largo tiempo
        
        Returns:
            (is_shadowbanned, confidence)
        """
        # Check impressions drop
        if metrics.impressions_received == 0 and metrics.posts_performed > 3:
            return True, 0.9  # High confidence
        
        # Check engagement rate
        if metrics.impressions_received > 100:
            engagement_rate = (
                (metrics.likes_received + metrics.comments_received) /
                metrics.impressions_received
            )
            
            if engagement_rate < 0.001:  # < 0.1%
                return True, 0.7  # Medium-high confidence
        
        # Check follow/view ratio
        follow_view_ratio = metrics.follow_view_ratio
        if follow_view_ratio < 0.001 and metrics.views_performed > 50:
            return True, 0.6  # Medium confidence
        
        return False, 0.0
    
    def detect_quality_issues(
        self,
        metrics: AccountWarmupMetrics
    ) -> list[str]:
        """
        Detecta problemas de calidad.
        
        Returns:
            Lista de issues encontrados
        """
        issues = []
        
        # Check block ratio
        if metrics.block_view_ratio > self.config.max_block_ratio:
            issues.append(f"High block ratio: {metrics.block_view_ratio:.2%}")
        
        # Check engagement ratio
        if metrics.impressions_received > 50:
            engagement_ratio = (
                (metrics.likes_received + metrics.comments_received) /
                metrics.impressions_received
            )
            
            if engagement_ratio < self.config.min_engagement_ratio:
                issues.append(f"Low engagement: {engagement_ratio:.2%}")
        
        # Check comment realism
        if metrics.comment_realism_score < 0.5 and metrics.comments_performed > 10:
            issues.append(f"Low comment realism: {metrics.comment_realism_score:.2f}")
        
        # Check session stability
        if metrics.session_stability_score < 0.6:
            issues.append(f"Unstable sessions: {metrics.session_stability_score:.2f}")
        
        return issues
    
    # ========================================================================
    # PUBLIC API - ACTION RECORDING
    # ========================================================================
    
    def record_action_performed(
        self,
        metrics: AccountWarmupMetrics,
        action_type: str,
        success: bool = True
    ):
        """
        Registra una acción realizada.
        
        Args:
            action_type: view, like, comment, follow, post
            success: Si la acción fue exitosa
        """
        if action_type == "view":
            metrics.views_performed += 1
        elif action_type == "like":
            metrics.likes_performed += 1
        elif action_type == "comment":
            metrics.comments_performed += 1
        elif action_type == "follow":
            metrics.follows_performed += 1
        elif action_type == "post":
            metrics.posts_performed += 1
        
        logger.debug(f"Recorded {action_type} ({'success' if success else 'failed'})")
    
    def record_engagement_received(
        self,
        metrics: AccountWarmupMetrics,
        engagement_type: str,
        count: int = 1
    ):
        """
        Registra engagement recibido.
        
        Args:
            engagement_type: impressions, likes, comments, follows, shares
            count: Cantidad recibida
        """
        if engagement_type == "impressions":
            metrics.impressions_received += count
        elif engagement_type == "likes":
            metrics.likes_received += count
        elif engagement_type == "comments":
            metrics.comments_received += count
        elif engagement_type == "follows":
            metrics.follows_received += count
        elif engagement_type == "shares":
            metrics.shares_received += count
        
        # Update ratios
        self._update_ratios(metrics)
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _calculate_quality_score(self, metrics: AccountWarmupMetrics) -> float:
        """Calcula quality score (0-1)"""
        
        scores = []
        
        # Follow/view ratio (higher = better)
        if metrics.follow_view_ratio > 0:
            fv_score = min(1.0, metrics.follow_view_ratio * 50)  # Normalize
            scores.append(fv_score)
        
        # Block/view ratio (lower = better)
        bv_score = 1.0 - min(1.0, metrics.block_view_ratio * 20)  # Inverse
        scores.append(bv_score)
        
        # Comment realism (0-1)
        scores.append(metrics.comment_realism_score)
        
        # Session stability (0-1)
        scores.append(metrics.session_stability_score)
        
        if not scores:
            return 0.5  # Default
        
        return sum(scores) / len(scores)
    
    def _update_ratios(self, metrics: AccountWarmupMetrics):
        """Actualiza los ratios calculados"""
        
        # Follow/view ratio
        if metrics.views_performed > 0:
            metrics.follow_view_ratio = metrics.follows_received / metrics.views_performed
        
        # Block/view ratio (simulated, would come from platform)
        # For now, keep it low
        metrics.block_view_ratio = 0.01


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_metrics_collector() -> AccountMetricsCollector:
    """Helper para crear metrics collector"""
    return AccountMetricsCollector()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MetricsCollectorConfig",
    "AccountMetricsCollector",
    "create_metrics_collector",
]
