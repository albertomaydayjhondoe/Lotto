"""
SPRINT 11 - Satellite Intelligence Optimization
Module: Sound Test Recommender

Planificador de A/B tests de sonidos para descubrir audio tracks
con mejor performance. Asigna cuentas a tracks, define duración,
y genera insights.
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .sat_intel_contracts import (
    SoundTestRecommendation,
    AccountProfile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class SoundTestConfig:
    """Configuración de sound testing"""
    
    # Test parameters
    min_accounts_per_track: int = 3
    max_accounts_per_track: int = 10
    min_posts_per_account: int = 2
    max_posts_per_account: int = 5
    
    # Test duration
    min_test_duration_hours: int = 24
    max_test_duration_hours: int = 168  # 1 week
    
    # Statistical significance
    min_samples_for_significance: int = 10


# ============================================================================
# SOUND TEST RECOMMENDER
# ============================================================================

class SoundTestRecommender:
    """
    Recomendador de A/B tests de audio tracks.
    
    Flujo:
    1. Recibe 2+ audio tracks a comparar
    2. Asigna cuentas a cada track (balanceado)
    3. Define duración del test
    4. Genera recomendación con expected insights
    """
    
    def __init__(self, config: Optional[SoundTestConfig] = None):
        self.config = config or SoundTestConfig()
        self._rng = random.Random()
        logger.info("SoundTestRecommender initialized")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def recommend_ab_test(
        self,
        track_a_id: str,
        track_b_id: str,
        available_accounts: List[AccountProfile],
        track_a_history: Optional[Dict[str, float]] = None,
        track_b_history: Optional[Dict[str, float]] = None
    ) -> SoundTestRecommendation:
        """
        Genera recomendación para A/B test de 2 tracks.
        
        Args:
            track_a_id: ID del track A
            track_b_id: ID del track B
            available_accounts: Cuentas disponibles para el test
            track_a_history: Performance histórica de track A
            track_b_history: Performance histórica de track B
        
        Returns:
            SoundTestRecommendation con configuración y expected insights
        """
        logger.info(f"Generating A/B test recommendation: {track_a_id} vs {track_b_id}")
        
        # 1. Calcular accounts per track
        total_accounts = len(available_accounts)
        
        if total_accounts < self.config.min_accounts_per_track * 2:
            logger.warning(f"Insufficient accounts ({total_accounts}) for balanced test")
            accounts_per_track = max(total_accounts // 2, 1)
        else:
            accounts_per_track = min(
                total_accounts // 2,
                self.config.max_accounts_per_track
            )
        
        # 2. Calcular posts per account
        posts_per_account = self._calculate_posts_per_account(
            accounts_per_track,
            track_a_history,
            track_b_history
        )
        
        # 3. Calcular test duration
        test_duration_hours = self._calculate_test_duration(
            accounts_per_track,
            posts_per_account
        )
        
        # 4. Generate rationale
        rationale = self._generate_rationale(
            track_a_id,
            track_b_id,
            accounts_per_track,
            posts_per_account,
            test_duration_hours,
            track_a_history,
            track_b_history
        )
        
        # 5. Expected insights
        expected_insights = self._generate_expected_insights(
            track_a_history,
            track_b_history
        )
        
        recommendation = SoundTestRecommendation(
            recommendation_id=f"st_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now(),
            track_a_id=track_a_id,
            track_b_id=track_b_id,
            accounts_per_track=accounts_per_track,
            posts_per_account=posts_per_account,
            test_duration_hours=test_duration_hours,
            rationale=rationale,
            expected_insights=expected_insights,
            track_a_historical_performance=track_a_history,
            track_b_historical_performance=track_b_history,
        )
        
        logger.debug(f"Recommendation: {accounts_per_track} accounts/track, "
                    f"{posts_per_account} posts/account, {test_duration_hours}h duration")
        
        return recommendation
    
    def recommend_multivariate_test(
        self,
        track_ids: List[str],
        available_accounts: List[AccountProfile],
        track_histories: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[SoundTestRecommendation]:
        """
        Genera recomendaciones para test multivariante (>2 tracks).
        
        Retorna lista de A/B tests pareados.
        """
        if len(track_ids) < 2:
            raise ValueError("Need at least 2 tracks for testing")
        
        logger.info(f"Generating multivariate test for {len(track_ids)} tracks")
        
        track_histories = track_histories or {}
        
        recommendations = []
        
        # Generate pairwise tests
        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                track_a = track_ids[i]
                track_b = track_ids[j]
                
                rec = self.recommend_ab_test(
                    track_a,
                    track_b,
                    available_accounts,
                    track_histories.get(track_a),
                    track_histories.get(track_b)
                )
                
                recommendations.append(rec)
        
        logger.info(f"Generated {len(recommendations)} pairwise tests")
        return recommendations
    
    def allocate_accounts_to_tracks(
        self,
        recommendation: SoundTestRecommendation,
        available_accounts: List[AccountProfile],
        ensure_niche_balance: bool = True
    ) -> Dict[str, List[str]]:
        """
        Asigna cuentas específicas a cada track.
        
        Args:
            recommendation: Recomendación de test
            available_accounts: Cuentas disponibles
            ensure_niche_balance: Si True, balancea nichos entre tracks
        
        Returns:
            Dict[track_id] = [account_ids]
        """
        accounts_needed = recommendation.accounts_per_track * 2
        
        if len(available_accounts) < accounts_needed:
            logger.warning(f"Insufficient accounts: {len(available_accounts)} < {accounts_needed}")
            # Use what we have
            accounts_needed = len(available_accounts)
        
        # Shuffle accounts for randomization
        shuffled = available_accounts.copy()
        self._rng.shuffle(shuffled)
        
        # If niche balance enabled, sort by niche first
        if ensure_niche_balance:
            shuffled = sorted(shuffled, key=lambda a: a.niche_id)
        
        # Split evenly
        mid = accounts_needed // 2
        
        track_a_accounts = [a.account_id for a in shuffled[:mid]]
        track_b_accounts = [a.account_id for a in shuffled[mid:accounts_needed]]
        
        allocation = {
            recommendation.track_a_id: track_a_accounts,
            recommendation.track_b_id: track_b_accounts,
        }
        
        logger.info(f"Allocated {len(track_a_accounts)} accounts to track A, "
                   f"{len(track_b_accounts)} accounts to track B")
        
        return allocation
    
    # ========================================================================
    # CALCULATION HELPERS
    # ========================================================================
    
    def _calculate_posts_per_account(
        self,
        accounts_per_track: int,
        track_a_history: Optional[Dict[str, float]],
        track_b_history: Optional[Dict[str, float]]
    ) -> int:
        """Calcula posts por cuenta necesarios para significancia estadística"""
        
        # Si hay data histórica con mucha varianza, necesitamos más samples
        if track_a_history and track_b_history:
            # TODO: Calcular varianza real
            # Por ahora: heurística simple
            return self.config.max_posts_per_account
        
        # Default: balance entre speed y statistical power
        total_samples = accounts_per_track * self.config.min_posts_per_account
        
        if total_samples >= self.config.min_samples_for_significance:
            return self.config.min_posts_per_account
        else:
            # Need more posts per account
            posts_needed = (self.config.min_samples_for_significance + accounts_per_track - 1) // accounts_per_track
            return min(posts_needed, self.config.max_posts_per_account)
    
    def _calculate_test_duration(
        self,
        accounts_per_track: int,
        posts_per_account: int
    ) -> int:
        """Calcula duración del test en horas"""
        
        # Asumiendo 1-2 posts por día por cuenta
        total_posts = accounts_per_track * posts_per_account
        
        # Estimate posting rate (conservative: 1 post per day per account)
        days_needed = posts_per_account
        
        hours_needed = days_needed * 24
        
        # Clamp to min/max
        return max(
            self.config.min_test_duration_hours,
            min(hours_needed, self.config.max_test_duration_hours)
        )
    
    # ========================================================================
    # RATIONALE & INSIGHTS
    # ========================================================================
    
    def _generate_rationale(
        self,
        track_a_id: str,
        track_b_id: str,
        accounts_per_track: int,
        posts_per_account: int,
        duration_hours: int,
        track_a_history: Optional[Dict[str, float]],
        track_b_history: Optional[Dict[str, float]]
    ) -> str:
        """Genera rationale human-readable"""
        
        parts = [
            f"A/B test comparing {track_a_id} vs {track_b_id}",
            f"{accounts_per_track} accounts per track",
            f"{posts_per_account} posts per account",
            f"{duration_hours}h duration (~{duration_hours // 24} days)",
        ]
        
        # Historical context
        if track_a_history:
            avg_a = track_a_history.get("avg_virality", 0.0)
            parts.append(f"Track A historical avg: {avg_a:.2f}")
        
        if track_b_history:
            avg_b = track_b_history.get("avg_virality", 0.0)
            parts.append(f"Track B historical avg: {avg_b:.2f}")
        
        return ". ".join(parts)
    
    def _generate_expected_insights(
        self,
        track_a_history: Optional[Dict[str, float]],
        track_b_history: Optional[Dict[str, float]]
    ) -> List[str]:
        """Genera lista de insights esperados del test"""
        
        insights = [
            "Which track drives higher retention",
            "Which track generates more engagement",
            "Niche-specific track preferences",
            "Optimal posting times per track",
        ]
        
        # Add historical context insights
        if track_a_history and track_b_history:
            avg_a = track_a_history.get("avg_virality", 0.0)
            avg_b = track_b_history.get("avg_virality", 0.0)
            
            if abs(avg_a - avg_b) > 0.2:
                insights.append(f"Validate historical difference (A={avg_a:.2f}, B={avg_b:.2f})")
            else:
                insights.append("Discover winner between similar performers")
        
        return insights


# ============================================================================
# ANALYSIS HELPERS
# ============================================================================

def analyze_test_results(
    track_a_results: List[Dict[str, float]],
    track_b_results: List[Dict[str, float]],
    significance_level: float = 0.05
) -> Dict:
    """
    Analiza resultados de un A/B test y determina ganador.
    
    Args:
        track_a_results: Lista de resultados para track A
        track_b_results: Lista de resultados para track B
        significance_level: Nivel de significancia estadística
    
    Returns:
        Dict con winner, confidence, metrics
    """
    # TODO: Implementar t-test real
    # Por ahora: simple comparison de promedios
    
    if not track_a_results or not track_b_results:
        return {
            "winner": None,
            "confidence": 0.0,
            "insufficient_data": True
        }
    
    # Calculate averages
    avg_a = sum(r.get("virality", 0.0) for r in track_a_results) / len(track_a_results)
    avg_b = sum(r.get("virality", 0.0) for r in track_b_results) / len(track_b_results)
    
    # Determine winner
    if avg_a > avg_b:
        winner = "track_a"
        lift = (avg_a - avg_b) / avg_b if avg_b > 0 else 0.0
    else:
        winner = "track_b"
        lift = (avg_b - avg_a) / avg_a if avg_a > 0 else 0.0
    
    # Confidence (placeholder - real implementation would use statistical test)
    confidence = 0.8 if abs(avg_a - avg_b) > 0.1 else 0.6
    
    return {
        "winner": winner,
        "track_a_avg": avg_a,
        "track_b_avg": avg_b,
        "lift": lift,
        "confidence": confidence,
        "sample_size_a": len(track_a_results),
        "sample_size_b": len(track_b_results),
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SoundTestConfig",
    "SoundTestRecommender",
    "analyze_test_results",
]
