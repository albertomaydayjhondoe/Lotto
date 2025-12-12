"""
Satellite ML Learning - Sprint 8
Aprendizaje ML cada 48h para optimización continua.

Detecta horarios óptimos, micro-momentos virales, y ajusta
comportamiento automáticamente basado en performance real.
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import statistics

logger = logging.getLogger(__name__)


class LearningPhase(Enum):
    """Fases del ciclo de aprendizaje."""
    COLLECTING = "collecting"      # Recolectando datos
    ANALYZING = "analyzing"         # Analizando patterns
    OPTIMIZING = "optimizing"       # Aplicando optimizaciones
    MONITORING = "monitoring"       # Monitoreando resultados


@dataclass
class PerformanceMetrics:
    """Métricas de performance de un post."""
    post_id: str
    account_id: str
    platform: str
    published_at: datetime
    
    # Engagement metrics
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    
    # Advanced metrics
    retention_rate: float = 0.0      # 0.0 - 1.0
    ctr: float = 0.0                 # Click-through rate
    completion_rate: float = 0.0     # Video completion %
    
    # Virality indicators
    viral_velocity: float = 0.0      # Views per hour first 24h
    engagement_rate: float = 0.0     # (likes + comments + shares) / views
    
    # Timing
    hour_published: int = 0
    day_of_week: int = 0             # 0=Monday, 6=Sunday
    
    def calculate_virality_score(self) -> float:
        """Calcula score de viralidad basado en métricas."""
        if self.views == 0:
            return 0.0
        
        # Weighted formula
        engagement_weight = 0.3
        retention_weight = 0.25
        velocity_weight = 0.25
        completion_weight = 0.2
        
        normalized_engagement = min(self.engagement_rate * 10, 1.0)
        normalized_velocity = min(self.viral_velocity / 10000, 1.0)
        
        score = (
            normalized_engagement * engagement_weight +
            self.retention_rate * retention_weight +
            normalized_velocity * velocity_weight +
            self.completion_rate * completion_weight
        )
        
        return score


@dataclass
class OptimalTiming:
    """Timing óptimo detectado."""
    hour: int
    day_of_week: int
    avg_virality_score: float
    sample_count: int
    confidence: float  # 0.0 - 1.0
    
    def __repr__(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"OptimalTiming({days[self.day_of_week]} {self.hour:02d}:00, score={self.avg_virality_score:.2f}, n={self.sample_count})"


@dataclass
class MicroMoment:
    """Micro-momento viral detectado."""
    timestamp: datetime
    account_id: str
    post_id: str
    virality_spike: float  # Magnitud del spike
    context: Dict[str, any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"MicroMoment({self.timestamp.isoformat()}, spike={self.virality_spike:.2f})"


@dataclass
class LearningCycle:
    """Ciclo de aprendizaje de 48h."""
    cycle_id: str
    start_time: datetime
    end_time: datetime
    phase: LearningPhase
    
    # Data collected
    metrics_collected: List[PerformanceMetrics] = field(default_factory=list)
    
    # Insights
    optimal_timings: List[OptimalTiming] = field(default_factory=list)
    micro_moments: List[MicroMoment] = field(default_factory=list)
    
    # Recommendations
    recommendations: Dict[str, any] = field(default_factory=dict)
    
    completed: bool = False
    completed_at: Optional[datetime] = None


class OptimalTimingAnalysis:
    """Análisis de timings óptimos."""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """Agrega métricas al historial."""
        self.metrics_history.append(metrics)
    
    def analyze_optimal_hours(
        self,
        min_samples: int = 5
    ) -> List[OptimalTiming]:
        """
        Analiza horarios óptimos basado en performance histórica.
        
        Args:
            min_samples: Mínimo de samples para considerar timing válido
            
        Returns:
            Lista de OptimalTiming ordenada por score
        """
        if len(self.metrics_history) < min_samples:
            return []
        
        # Group by (hour, day_of_week)
        timing_groups: Dict[Tuple[int, int], List[float]] = {}
        
        for metric in self.metrics_history:
            key = (metric.hour_published, metric.day_of_week)
            virality_score = metric.calculate_virality_score()
            
            if key not in timing_groups:
                timing_groups[key] = []
            timing_groups[key].append(virality_score)
        
        # Calculate averages
        optimal_timings = []
        
        for (hour, day), scores in timing_groups.items():
            if len(scores) >= min_samples:
                avg_score = statistics.mean(scores)
                stdev = statistics.stdev(scores) if len(scores) > 1 else 0
                
                # Confidence: higher samples + lower stdev = higher confidence
                confidence = min(len(scores) / 20, 1.0) * (1.0 - min(stdev, 0.5))
                
                optimal_timings.append(OptimalTiming(
                    hour=hour,
                    day_of_week=day,
                    avg_virality_score=avg_score,
                    sample_count=len(scores),
                    confidence=confidence
                ))
        
        # Sort by score
        optimal_timings.sort(key=lambda x: x.avg_virality_score, reverse=True)
        
        return optimal_timings
    
    def get_best_timing(self, day_of_week: int) -> Optional[OptimalTiming]:
        """Obtiene mejor timing para día específico."""
        timings = self.analyze_optimal_hours()
        
        day_timings = [t for t in timings if t.day_of_week == day_of_week]
        if day_timings:
            return day_timings[0]
        return None


class MicroMomentDetector:
    """Detector de micro-momentos virales."""
    
    SPIKE_THRESHOLD = 2.0  # 2x el promedio
    
    def __init__(self):
        self.detected_moments: List[MicroMoment] = []
    
    def detect_spikes(
        self,
        metrics_stream: List[PerformanceMetrics]
    ) -> List[MicroMoment]:
        """
        Detecta spikes virales en stream de métricas.
        
        Args:
            metrics_stream: Stream de métricas ordenadas por tiempo
            
        Returns:
            Lista de MicroMoment detectados
        """
        if len(metrics_stream) < 10:
            return []
        
        # Calculate baseline (promedio de últimos N posts)
        recent_scores = [m.calculate_virality_score() for m in metrics_stream[-20:]]
        baseline = statistics.mean(recent_scores) if recent_scores else 0.5
        
        moments = []
        
        for metric in metrics_stream[-10:]:  # Últimos 10 posts
            virality_score = metric.calculate_virality_score()
            
            # Spike detection
            if virality_score > baseline * self.SPIKE_THRESHOLD:
                spike_magnitude = virality_score / baseline if baseline > 0 else virality_score
                
                moment = MicroMoment(
                    timestamp=metric.published_at,
                    account_id=metric.account_id,
                    post_id=metric.post_id,
                    virality_spike=spike_magnitude,
                    context={
                        "hour": metric.hour_published,
                        "day": metric.day_of_week,
                        "views": metric.views,
                        "engagement_rate": metric.engagement_rate
                    }
                )
                
                moments.append(moment)
                self.detected_moments.append(moment)
        
        return moments


class BehaviorOptimizer:
    """Optimizador de comportamiento basado en aprendizaje."""
    
    def __init__(self):
        self.optimizations_applied: List[Dict] = []
    
    def generate_recommendations(
        self,
        optimal_timings: List[OptimalTiming],
        micro_moments: List[MicroMoment],
        current_behavior: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Genera recomendaciones de optimización.
        
        Args:
            optimal_timings: Timings óptimos detectados
            micro_moments: Micro-momentos detectados
            current_behavior: Comportamiento actual
            
        Returns:
            Dict con recomendaciones
        """
        recommendations = {
            "adjust_posting_hours": [],
            "increase_frequency_on": [],
            "decrease_frequency_on": [],
            "focus_days": [],
            "avoid_hours": []
        }
        
        # 1. Adjust posting hours
        if optimal_timings:
            top_3 = optimal_timings[:3]
            recommendations["adjust_posting_hours"] = [
                {
                    "hour": t.hour,
                    "day": t.day_of_week,
                    "score": t.avg_virality_score,
                    "confidence": t.confidence
                }
                for t in top_3
            ]
        
        # 2. Focus days (days with most micro-moments)
        if micro_moments:
            day_counts = {}
            for moment in micro_moments:
                day = moment.timestamp.weekday()
                day_counts[day] = day_counts.get(day, 0) + 1
            
            if day_counts:
                best_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:2]
                recommendations["focus_days"] = [day for day, count in best_days]
        
        # 3. Avoid hours (hours with consistently low performance)
        if optimal_timings:
            bottom_timings = [t for t in optimal_timings if t.avg_virality_score < 0.3]
            if bottom_timings:
                recommendations["avoid_hours"] = list(set(t.hour for t in bottom_timings))
        
        return recommendations
    
    def apply_optimizations(
        self,
        account_id: str,
        recommendations: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Aplica optimizaciones al comportamiento de cuenta.
        
        En producción, esto actualizaría:
        - BehaviorEngine schedules
        - WarmupEngine targets
        - ContentRouter priorities
        
        Returns:
            Dict con optimizaciones aplicadas
        """
        optimizations = {
            "account_id": account_id,
            "timestamp": datetime.now().isoformat(),
            "changes": []
        }
        
        # Apply hour adjustments
        if recommendations.get("adjust_posting_hours"):
            optimizations["changes"].append({
                "type": "posting_hours",
                "hours": [h["hour"] for h in recommendations["adjust_posting_hours"]],
                "reason": "Optimal timing detected"
            })
        
        # Apply focus days
        if recommendations.get("focus_days"):
            optimizations["changes"].append({
                "type": "focus_days",
                "days": recommendations["focus_days"],
                "reason": "High viral activity"
            })
        
        self.optimizations_applied.append(optimizations)
        
        logger.info(f"Applied {len(optimizations['changes'])} optimizations to {account_id}")
        return optimizations


class SatelliteMLLearning:
    """
    Motor de ML Learning para satellite accounts.
    
    Features:
    - Ciclos de aprendizaje cada 48h
    - Detección de horarios óptimos
    - Detección de micro-momentos virales
    - Optimización automática de comportamiento
    - Recomendaciones basadas en data
    """
    
    CYCLE_DURATION_HOURS = 48
    
    def __init__(self):
        self.timing_analysis = OptimalTimingAnalysis()
        self.moment_detector = MicroMomentDetector()
        self.behavior_optimizer = BehaviorOptimizer()
        
        self.learning_cycles: List[LearningCycle] = []
        self.current_cycle: Optional[LearningCycle] = None
        
        logger.info("SatelliteMLLearning initialized")
    
    def start_learning_cycle(self) -> LearningCycle:
        """Inicia nuevo ciclo de aprendizaje de 48h."""
        now = datetime.now()
        cycle_id = f"cycle_{now.timestamp()}"
        
        cycle = LearningCycle(
            cycle_id=cycle_id,
            start_time=now,
            end_time=now + timedelta(hours=self.CYCLE_DURATION_HOURS),
            phase=LearningPhase.COLLECTING
        )
        
        self.current_cycle = cycle
        self.learning_cycles.append(cycle)
        
        logger.info(f"Started learning cycle: {cycle_id} (48h)")
        return cycle
    
    def record_performance(self, metrics: PerformanceMetrics):
        """
        Registra performance de un post.
        
        Args:
            metrics: PerformanceMetrics del post
        """
        # Add to timing analysis
        self.timing_analysis.add_metrics(metrics)
        
        # Add to current cycle
        if self.current_cycle and not self.current_cycle.completed:
            self.current_cycle.metrics_collected.append(metrics)
            
            logger.info(f"Recorded performance: {metrics.post_id} (score={metrics.calculate_virality_score():.2f})")
    
    def analyze_cycle(self, cycle: LearningCycle) -> LearningCycle:
        """
        Analiza ciclo de aprendizaje completado.
        
        Args:
            cycle: LearningCycle a analizar
            
        Returns:
            LearningCycle con insights
        """
        cycle.phase = LearningPhase.ANALYZING
        
        # 1. Analyze optimal timings
        optimal_timings = self.timing_analysis.analyze_optimal_hours(min_samples=3)
        cycle.optimal_timings = optimal_timings
        
        logger.info(f"Detected {len(optimal_timings)} optimal timings")
        
        # 2. Detect micro-moments
        micro_moments = self.moment_detector.detect_spikes(cycle.metrics_collected)
        cycle.micro_moments = micro_moments
        
        logger.info(f"Detected {len(micro_moments)} micro-moments")
        
        # 3. Generate recommendations
        recommendations = self.behavior_optimizer.generate_recommendations(
            optimal_timings,
            micro_moments,
            current_behavior={}
        )
        cycle.recommendations = recommendations
        
        cycle.phase = LearningPhase.OPTIMIZING
        cycle.completed = True
        cycle.completed_at = datetime.now()
        
        logger.info(f"Cycle {cycle.cycle_id} analysis completed")
        return cycle
    
    def get_optimal_timing_for_account(
        self,
        account_id: str,
        day_of_week: int
    ) -> Optional[OptimalTiming]:
        """Obtiene timing óptimo para cuenta en día específico."""
        return self.timing_analysis.get_best_timing(day_of_week)
    
    def get_recommendations(self, account_id: str) -> Dict[str, any]:
        """Obtiene recomendaciones actuales para cuenta."""
        if self.current_cycle and self.current_cycle.recommendations:
            return self.current_cycle.recommendations
        
        # Get from last completed cycle
        completed_cycles = [c for c in self.learning_cycles if c.completed]
        if completed_cycles:
            return completed_cycles[-1].recommendations
        
        return {}
    
    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del ML learning."""
        total_cycles = len(self.learning_cycles)
        completed = sum(1 for c in self.learning_cycles if c.completed)
        
        total_metrics = len(self.timing_analysis.metrics_history)
        total_moments = len(self.moment_detector.detected_moments)
        total_optimizations = len(self.behavior_optimizer.optimizations_applied)
        
        return {
            "total_cycles": total_cycles,
            "completed_cycles": completed,
            "active_cycle": self.current_cycle.cycle_id if self.current_cycle else None,
            "total_metrics_recorded": total_metrics,
            "micro_moments_detected": total_moments,
            "optimizations_applied": total_optimizations,
            "optimal_timings_known": len(self.timing_analysis.analyze_optimal_hours())
        }
