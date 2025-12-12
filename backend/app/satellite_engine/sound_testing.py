"""
Sound Testing Engine - Sprint 8
Prueba A/B de sonidos con medición de viralidad.

Prueba sonidos nuevos en cuentas satélite, mide viralidad/CTR/retención,
compara en paralelo, identifica qué sonidos suben mejor.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import statistics

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Estados de test A/B."""
    SETUP = "setup"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SoundWinner(Enum):
    """Ganador del A/B test."""
    SOUND_A = "sound_a"
    SOUND_B = "sound_b"
    TIE = "tie"
    UNDETERMINED = "undetermined"


@dataclass
class SoundMetrics:
    """Métricas de un sonido."""
    sound_id: str
    sound_name: str
    
    # Engagement
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_saves: int = 0
    
    # Performance
    avg_ctr: float = 0.0
    avg_retention: float = 0.0
    avg_completion_rate: float = 0.0
    viral_coefficient: float = 0.0  # shares per view
    
    # Posts
    posts_count: int = 0
    posts_ids: List[str] = field(default_factory=list)
    
    def calculate_virality_score(self) -> float:
        """Calcula score de viralidad total."""
        if self.total_views == 0:
            return 0.0
        
        engagement_rate = (
            (self.total_likes + self.total_comments + self.total_shares + self.total_saves)
            / self.total_views
        )
        
        # Weighted formula
        score = (
            engagement_rate * 0.3 +
            self.avg_retention * 0.25 +
            self.viral_coefficient * 100 * 0.25 +
            self.avg_completion_rate * 0.2
        )
        
        return min(score, 1.0)
    
    def get_engagement_rate(self) -> float:
        """Calcula engagement rate."""
        if self.total_views == 0:
            return 0.0
        return (self.total_likes + self.total_comments + self.total_shares) / self.total_views


@dataclass
class ABTestConfig:
    """Configuración de test A/B."""
    sound_a_id: str
    sound_a_name: str
    sound_b_id: str
    sound_b_name: str
    
    # Test parameters
    accounts_per_sound: int = 5
    posts_per_account: int = 3
    test_duration_hours: int = 72  # 3 días
    
    # Targeting
    target_niche: Optional[str] = None
    target_platform: str = "tiktok"
    
    # Success criteria
    min_views_threshold: int = 1000
    significance_threshold: float = 0.15  # 15% difference


@dataclass
class SoundTest:
    """Test A/B de sonidos."""
    test_id: str
    config: ABTestConfig
    
    start_time: datetime
    end_time: datetime
    status: TestStatus = TestStatus.SETUP
    
    # Metrics
    sound_a_metrics: Optional[SoundMetrics] = None
    sound_b_metrics: Optional[SoundMetrics] = None
    
    # Accounts assigned
    sound_a_accounts: List[str] = field(default_factory=list)
    sound_b_accounts: List[str] = field(default_factory=list)
    
    # Results
    winner: SoundWinner = SoundWinner.UNDETERMINED
    confidence: float = 0.0
    winner_reason: str = ""
    
    completed_at: Optional[datetime] = None


@dataclass
class ABTestResult:
    """Resultado de test A/B."""
    test: SoundTest
    
    winner: SoundWinner
    winner_sound_id: Optional[str] = None
    winner_sound_name: Optional[str] = None
    
    # Performance comparison
    sound_a_score: float = 0.0
    sound_b_score: float = 0.0
    difference_percentage: float = 0.0
    
    # Statistical significance
    is_significant: bool = False
    confidence: float = 0.0
    
    # Recommendation
    recommendation: str = ""
    
    def __repr__(self):
        return f"ABTestResult(winner={self.winner.value}, diff={self.difference_percentage:.1f}%, significant={self.is_significant})"


class SoundTestingEngine:
    """
    Motor de pruebas A/B para sonidos.
    
    Features:
    - A/B testing de sonidos en paralelo
    - Medición de viralidad/CTR/retención
    - Comparación estadística
    - Identificación de ganadores
    - Integración con Orchestrator
    """
    
    def __init__(self):
        self.active_tests: Dict[str, SoundTest] = {}
        self.completed_tests: List[SoundTest] = []
        
        logger.info("SoundTestingEngine initialized")
    
    def create_ab_test(
        self,
        sound_a_id: str,
        sound_a_name: str,
        sound_b_id: str,
        sound_b_name: str,
        accounts_pool: List[str],
        config: Optional[ABTestConfig] = None
    ) -> SoundTest:
        """
        Crea test A/B de sonidos.
        
        Args:
            sound_a_id: ID de sonido A
            sound_a_name: Nombre de sonido A
            sound_b_id: ID de sonido B
            sound_b_name: Nombre de sonido B
            accounts_pool: Pool de cuentas disponibles
            config: Configuración custom (opcional)
            
        Returns:
            SoundTest configurado
        """
        # Default config
        if not config:
            config = ABTestConfig(
                sound_a_id=sound_a_id,
                sound_a_name=sound_a_name,
                sound_b_id=sound_b_id,
                sound_b_name=sound_b_name
            )
        
        # Validate accounts pool
        required_accounts = config.accounts_per_sound * 2
        if len(accounts_pool) < required_accounts:
            raise ValueError(f"Need {required_accounts} accounts, got {len(accounts_pool)}")
        
        # Generate test ID
        test_id = f"test_{datetime.now().timestamp()}"
        
        # Assign accounts randomly
        shuffled = accounts_pool.copy()
        random.shuffle(shuffled)
        
        sound_a_accounts = shuffled[:config.accounts_per_sound]
        sound_b_accounts = shuffled[config.accounts_per_sound:required_accounts]
        
        # Create test
        now = datetime.now()
        test = SoundTest(
            test_id=test_id,
            config=config,
            start_time=now,
            end_time=now + timedelta(hours=config.test_duration_hours),
            sound_a_accounts=sound_a_accounts,
            sound_b_accounts=sound_b_accounts
        )
        
        # Initialize metrics
        test.sound_a_metrics = SoundMetrics(
            sound_id=sound_a_id,
            sound_name=sound_a_name
        )
        test.sound_b_metrics = SoundMetrics(
            sound_id=sound_b_id,
            sound_name=sound_b_name
        )
        
        # Store test
        self.active_tests[test_id] = test
        
        logger.info(f"Created A/B test: {test_id} ({sound_a_name} vs {sound_b_name})")
        logger.info(f"  Sound A accounts: {sound_a_accounts}")
        logger.info(f"  Sound B accounts: {sound_b_accounts}")
        
        return test
    
    def start_test(self, test_id: str) -> SoundTest:
        """Inicia test A/B."""
        test = self.active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.status = TestStatus.RUNNING
        test.start_time = datetime.now()
        
        logger.info(f"Started A/B test: {test_id}")
        return test
    
    def record_post_performance(
        self,
        test_id: str,
        sound_id: str,
        post_id: str,
        views: int,
        likes: int,
        comments: int,
        shares: int,
        saves: int,
        ctr: float,
        retention: float,
        completion_rate: float
    ):
        """
        Registra performance de un post del test.
        
        Args:
            test_id: ID del test
            sound_id: ID del sonido
            post_id: ID del post
            views, likes, comments, shares, saves: Métricas
            ctr: Click-through rate
            retention: Retention rate
            completion_rate: Completion rate
        """
        test = self.active_tests.get(test_id)
        if not test:
            logger.warning(f"Test {test_id} not found")
            return
        
        # Determine which sound
        if sound_id == test.config.sound_a_id:
            metrics = test.sound_a_metrics
        elif sound_id == test.config.sound_b_id:
            metrics = test.sound_b_metrics
        else:
            logger.error(f"Sound {sound_id} not in test {test_id}")
            return
        
        # Update metrics
        metrics.total_views += views
        metrics.total_likes += likes
        metrics.total_comments += comments
        metrics.total_shares += shares
        metrics.total_saves += saves
        metrics.posts_count += 1
        metrics.posts_ids.append(post_id)
        
        # Update averages
        n = metrics.posts_count
        metrics.avg_ctr = (metrics.avg_ctr * (n - 1) + ctr) / n
        metrics.avg_retention = (metrics.avg_retention * (n - 1) + retention) / n
        metrics.avg_completion_rate = (metrics.avg_completion_rate * (n - 1) + completion_rate) / n
        
        if metrics.total_views > 0:
            metrics.viral_coefficient = metrics.total_shares / metrics.total_views
        
        logger.info(f"Recorded post {post_id} for sound {sound_id}: {views} views, {likes} likes")
    
    def analyze_test(self, test_id: str) -> ABTestResult:
        """
        Analiza resultados del test y determina ganador.
        
        Args:
            test_id: ID del test
            
        Returns:
            ABTestResult con ganador y análisis
        """
        test = self.active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        sound_a = test.sound_a_metrics
        sound_b = test.sound_b_metrics
        
        # Check if enough data
        if sound_a.total_views < test.config.min_views_threshold:
            logger.warning(f"Sound A has insufficient views: {sound_a.total_views}")
        if sound_b.total_views < test.config.min_views_threshold:
            logger.warning(f"Sound B has insufficient views: {sound_b.total_views}")
        
        # Calculate virality scores
        score_a = sound_a.calculate_virality_score()
        score_b = sound_b.calculate_virality_score()
        
        # Calculate difference
        if score_a + score_b > 0:
            diff_percentage = abs(score_a - score_b) / max(score_a, score_b) * 100
        else:
            diff_percentage = 0
        
        # Determine winner
        is_significant = diff_percentage >= (test.config.significance_threshold * 100)
        
        if not is_significant:
            winner = SoundWinner.TIE
            winner_sound_id = None
            winner_sound_name = None
            recommendation = "No significant difference. Both sounds perform similarly."
        elif score_a > score_b:
            winner = SoundWinner.SOUND_A
            winner_sound_id = sound_a.sound_id
            winner_sound_name = sound_a.sound_name
            recommendation = f"Use {sound_a.sound_name} - {diff_percentage:.1f}% better performance"
        else:
            winner = SoundWinner.SOUND_B
            winner_sound_id = sound_b.sound_id
            winner_sound_name = sound_b.sound_name
            recommendation = f"Use {sound_b.sound_name} - {diff_percentage:.1f}% better performance"
        
        # Calculate confidence
        total_posts = sound_a.posts_count + sound_b.posts_count
        min_posts = test.config.accounts_per_sound * test.config.posts_per_account * 2
        confidence = min(total_posts / min_posts, 1.0)
        
        # Create result
        result = ABTestResult(
            test=test,
            winner=winner,
            winner_sound_id=winner_sound_id,
            winner_sound_name=winner_sound_name,
            sound_a_score=score_a,
            sound_b_score=score_b,
            difference_percentage=diff_percentage,
            is_significant=is_significant,
            confidence=confidence,
            recommendation=recommendation
        )
        
        # Update test
        test.winner = winner
        test.confidence = confidence
        test.winner_reason = recommendation
        test.status = TestStatus.COMPLETED
        test.completed_at = datetime.now()
        
        logger.info(f"Test {test_id} analyzed: {winner.value} (diff={diff_percentage:.1f}%)")
        
        return result
    
    def complete_test(self, test_id: str) -> ABTestResult:
        """Completa test y retorna resultado."""
        result = self.analyze_test(test_id)
        
        # Move to completed
        test = self.active_tests.pop(test_id)
        self.completed_tests.append(test)
        
        logger.info(f"Test {test_id} completed and archived")
        return result
    
    def get_test(self, test_id: str) -> Optional[SoundTest]:
        """Obtiene test activo."""
        return self.active_tests.get(test_id)
    
    def get_test_progress(self, test_id: str) -> Dict[str, any]:
        """Obtiene progreso de test."""
        test = self.active_tests.get(test_id)
        if not test:
            return {"error": "Test not found"}
        
        time_elapsed = (datetime.now() - test.start_time).total_seconds() / 3600
        time_remaining = max(0, test.config.test_duration_hours - time_elapsed)
        progress = min(time_elapsed / test.config.test_duration_hours * 100, 100)
        
        return {
            "test_id": test_id,
            "status": test.status.value,
            "progress_percentage": progress,
            "hours_elapsed": time_elapsed,
            "hours_remaining": time_remaining,
            "sound_a": {
                "name": test.sound_a_metrics.sound_name,
                "posts": test.sound_a_metrics.posts_count,
                "views": test.sound_a_metrics.total_views,
                "engagement_rate": test.sound_a_metrics.get_engagement_rate(),
                "virality_score": test.sound_a_metrics.calculate_virality_score()
            },
            "sound_b": {
                "name": test.sound_b_metrics.sound_name,
                "posts": test.sound_b_metrics.posts_count,
                "views": test.sound_b_metrics.total_views,
                "engagement_rate": test.sound_b_metrics.get_engagement_rate(),
                "virality_score": test.sound_b_metrics.calculate_virality_score()
            }
        }
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del sound testing."""
        total_tests = len(self.active_tests) + len(self.completed_tests)
        
        winners = {
            "sound_a": 0,
            "sound_b": 0,
            "tie": 0
        }
        
        for test in self.completed_tests:
            if test.winner == SoundWinner.SOUND_A:
                winners["sound_a"] += 1
            elif test.winner == SoundWinner.SOUND_B:
                winners["sound_b"] += 1
            elif test.winner == SoundWinner.TIE:
                winners["tie"] += 1
        
        return {
            "total_tests": total_tests,
            "active_tests": len(self.active_tests),
            "completed_tests": len(self.completed_tests),
            "winners_distribution": winners
        }
