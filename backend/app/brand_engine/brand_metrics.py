"""
Brand Metrics Analyzer - Real Performance Data Analysis (Sprint 4)

Analiza métricas REALES de contenido para identificar patrones de rendimiento.

Características:
- Analiza datos reales: retention, CTR, watch time, engagement
- Correlaciones estética-rendimiento
- Identifica mejores escenas, colores, formatos
- NO asume nada sobre qué funciona - lo descubre de los datos
- Statistical confidence para validar patrones

Output: MetricInsights con patrones data-driven para reglas de marca.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
import statistics

from .models import (
    ContentPerformance,
    MetricInsights,
)

logger = logging.getLogger(__name__)


class BrandMetricsAnalyzer:
    """
    Analyzes real content performance to identify what works.
    
    Data-driven approach - NO assumptions about what content performs well.
    Everything learned from actual metrics.
    """
    
    def __init__(self, min_sample_size: int = 10):
        """
        Initialize metrics analyzer.
        
        Args:
            min_sample_size: Minimum content samples needed for statistical confidence
        """
        self.min_sample_size = min_sample_size
        self.content_data: List[ContentPerformance] = []
    
    # ========================================
    # Data Loading
    # ========================================
    
    def add_content_performance(self, performance: ContentPerformance) -> None:
        """
        Add content performance data.
        
        Args:
            performance: Performance metrics for a piece of content
        """
        self.content_data.append(performance)
        logger.debug(f"Added performance data for {performance.content_id}")
    
    def add_batch_performance(self, performances: List[ContentPerformance]) -> None:
        """Add multiple content performance records."""
        self.content_data.extend(performances)
        logger.info(f"Added {len(performances)} performance records. Total: {len(self.content_data)}")
    
    def load_from_database(self, db_client: Any, artist_id: str, days_back: int = 90) -> int:
        """
        Load performance data from database.
        
        Args:
            db_client: Database client (implementation-specific)
            artist_id: Artist identifier
            days_back: How many days of historical data to load
            
        Returns:
            Number of records loaded
        """
        # Placeholder for database integration
        # In production, this would query actual performance DB
        logger.info(f"Loading performance data for artist {artist_id} from last {days_back} days")
        
        # TODO: Implement actual DB query
        # Example:
        # cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        # records = db_client.query_content_performance(artist_id, cutoff_date)
        # self.add_batch_performance(records)
        
        return len(self.content_data)
    
    # ========================================
    # Performance Analysis
    # ========================================
    
    def analyze_engagement_metrics(self) -> Dict[str, float]:
        """
        Calculate baseline engagement metrics.
        
        Returns:
            Dict with average metrics
        """
        if not self.content_data:
            return {}
        
        total_views = sum(c.views for c in self.content_data)
        total_likes = sum(c.likes for c in self.content_data)
        total_comments = sum(c.comments for c in self.content_data)
        total_shares = sum(c.shares for c in self.content_data)
        
        avg_engagement_rate = 0.0
        if total_views > 0:
            total_engagements = total_likes + total_comments + total_shares
            avg_engagement_rate = total_engagements / total_views
        
        return {
            "avg_views": total_views / len(self.content_data),
            "avg_likes": total_likes / len(self.content_data),
            "avg_comments": total_comments / len(self.content_data),
            "avg_shares": total_shares / len(self.content_data),
            "avg_engagement_rate": avg_engagement_rate,
        }
    
    def analyze_retention_metrics(self) -> Dict[str, float]:
        """
        Calculate baseline retention metrics.
        
        Returns:
            Dict with average retention metrics
        """
        if not self.content_data:
            return {}
        
        retention_rates = [c.retention_rate for c in self.content_data if c.retention_rate > 0]
        completion_rates = [c.completion_rate for c in self.content_data if c.completion_rate > 0]
        skip_rates = [c.skip_rate for c in self.content_data if c.skip_rate > 0]
        watch_times = [c.avg_watch_time_seconds for c in self.content_data if c.avg_watch_time_seconds > 0]
        
        return {
            "avg_retention_rate": statistics.mean(retention_rates) if retention_rates else 0.0,
            "median_retention_rate": statistics.median(retention_rates) if retention_rates else 0.0,
            "avg_completion_rate": statistics.mean(completion_rates) if completion_rates else 0.0,
            "avg_skip_rate": statistics.mean(skip_rates) if skip_rates else 0.0,
            "avg_watch_time_seconds": statistics.mean(watch_times) if watch_times else 0.0,
        }
    
    def analyze_ctr_metrics(self) -> Dict[str, float]:
        """
        Calculate click-through metrics.
        
        Returns:
            Dict with CTR metrics
        """
        if not self.content_data:
            return {}
        
        ctr_values = [c.ctr for c in self.content_data if c.ctr > 0]
        
        return {
            "avg_ctr": statistics.mean(ctr_values) if ctr_values else 0.0,
            "median_ctr": statistics.median(ctr_values) if ctr_values else 0.0,
        }
    
    # ========================================
    # Scene Performance Analysis
    # ========================================
    
    def analyze_scene_performance(self) -> List[Dict[str, Any]]:
        """
        Identify which scenes perform best.
        
        NO assumptions - purely data-driven.
        
        Returns:
            List of scenes ranked by performance
        """
        if len(self.content_data) < self.min_sample_size:
            logger.warning(f"Insufficient data for scene analysis: {len(self.content_data)} < {self.min_sample_size}")
            return []
        
        # Group content by scene
        scene_groups: Dict[str, List[ContentPerformance]] = defaultdict(list)
        for content in self.content_data:
            if content.dominant_scene:
                scene_groups[content.dominant_scene].append(content)
        
        # Calculate average metrics per scene
        scene_performance = []
        for scene, contents in scene_groups.items():
            if len(contents) < 3:  # Need at least 3 samples per scene
                continue
            
            avg_retention = statistics.mean([c.retention_rate for c in contents if c.retention_rate > 0])
            avg_engagement = statistics.mean([
                (c.likes + c.comments + c.shares) / c.views if c.views > 0 else 0
                for c in contents
            ])
            avg_completion = statistics.mean([c.completion_rate for c in contents if c.completion_rate > 0])
            
            # Combined performance score
            performance_score = (avg_retention * 0.4) + (avg_engagement * 0.3) + (avg_completion * 0.3)
            
            scene_performance.append({
                "scene": scene,
                "count": len(contents),
                "avg_retention": round(avg_retention, 3),
                "avg_engagement": round(avg_engagement, 4),
                "avg_completion": round(avg_completion, 3),
                "performance_score": round(performance_score, 3),
            })
        
        # Sort by performance score
        scene_performance.sort(key=lambda x: x["performance_score"], reverse=True)
        
        logger.info(f"Analyzed {len(scene_performance)} scenes from {len(self.content_data)} content pieces")
        
        return scene_performance
    
    # ========================================
    # Color Performance Analysis
    # ========================================
    
    def analyze_color_performance(self) -> List[Dict[str, Any]]:
        """
        Identify which color palettes perform best.
        
        NO assumptions - learned from data.
        
        Returns:
            List of color palettes ranked by performance
        """
        if len(self.content_data) < self.min_sample_size:
            logger.warning(f"Insufficient data for color analysis: {len(self.content_data)} < {self.min_sample_size}")
            return []
        
        # Group content by dominant color
        color_groups: Dict[str, List[ContentPerformance]] = defaultdict(list)
        for content in self.content_data:
            if content.dominant_colors and len(content.dominant_colors) > 0:
                # Use first dominant color
                primary_color = content.dominant_colors[0]
                color_groups[primary_color].append(content)
        
        # Calculate average metrics per color
        color_performance = []
        for color, contents in color_groups.items():
            if len(contents) < 3:  # Need at least 3 samples per color
                continue
            
            avg_retention = statistics.mean([c.retention_rate for c in contents if c.retention_rate > 0])
            avg_engagement = statistics.mean([
                (c.likes + c.comments + c.shares) / c.views if c.views > 0 else 0
                for c in contents
            ])
            
            performance_score = (avg_retention * 0.6) + (avg_engagement * 0.4)
            
            color_performance.append({
                "color": color,
                "count": len(contents),
                "avg_retention": round(avg_retention, 3),
                "avg_engagement": round(avg_engagement, 4),
                "performance_score": round(performance_score, 3),
            })
        
        # Sort by performance
        color_performance.sort(key=lambda x: x["performance_score"], reverse=True)
        
        logger.info(f"Analyzed {len(color_performance)} color palettes")
        
        return color_performance
    
    # ========================================
    # Content Format Analysis
    # ========================================
    
    def analyze_format_performance(self) -> List[Dict[str, Any]]:
        """
        Identify which content formats/types perform best.
        
        Returns:
            List of formats ranked by performance
        """
        if len(self.content_data) < self.min_sample_size:
            return []
        
        # Group by content type
        format_groups: Dict[str, List[ContentPerformance]] = defaultdict(list)
        for content in self.content_data:
            format_groups[content.content_type].append(content)
        
        # Calculate metrics per format
        format_performance = []
        for format_type, contents in format_groups.items():
            if len(contents) < 3:
                continue
            
            avg_retention = statistics.mean([c.retention_rate for c in contents if c.retention_rate > 0])
            avg_completion = statistics.mean([c.completion_rate for c in contents if c.completion_rate > 0])
            avg_ctr = statistics.mean([c.ctr for c in contents if c.ctr > 0])
            
            format_performance.append({
                "format": format_type,
                "count": len(contents),
                "avg_retention": round(avg_retention, 3),
                "avg_completion": round(avg_completion, 3),
                "avg_ctr": round(avg_ctr, 4),
            })
        
        format_performance.sort(key=lambda x: x["avg_retention"], reverse=True)
        
        return format_performance
    
    # ========================================
    # Correlation Analysis
    # ========================================
    
    def calculate_aesthetic_performance_correlation(self) -> Dict[str, float]:
        """
        Calculate correlation between aesthetic features and performance.
        
        Uses aesthetic_score from content (if available).
        
        Returns:
            Correlation coefficients
        """
        if len(self.content_data) < self.min_sample_size:
            return {}
        
        # Filter content with aesthetic scores
        scored_content = [c for c in self.content_data if c.aesthetic_score is not None]
        if len(scored_content) < self.min_sample_size:
            logger.warning(f"Insufficient aesthetic scores: {len(scored_content)}")
            return {}
        
        # Calculate correlations
        aesthetic_scores = [c.aesthetic_score for c in scored_content]
        retention_rates = [c.retention_rate for c in scored_content]
        engagement_rates = [
            (c.likes + c.comments + c.shares) / c.views if c.views > 0 else 0
            for c in scored_content
        ]
        
        # Simple Pearson correlation
        aesthetic_retention_corr = self._calculate_correlation(aesthetic_scores, retention_rates)
        aesthetic_engagement_corr = self._calculate_correlation(aesthetic_scores, engagement_rates)
        
        return {
            "aesthetic_retention_correlation": round(aesthetic_retention_corr, 3),
            "aesthetic_engagement_correlation": round(aesthetic_engagement_corr, 3),
        }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient.
        
        Args:
            x: First variable
            y: Second variable
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        denominator = (denominator_x * denominator_y) ** 0.5
        correlation = numerator / denominator
        
        return correlation
    
    # ========================================
    # Top Performers Identification
    # ========================================
    
    def identify_top_performers(self, top_n: int = 10) -> List[str]:
        """
        Identify top performing content IDs.
        
        Uses combined score of retention, engagement, and completion.
        
        Args:
            top_n: Number of top performers to return
            
        Returns:
            List of content IDs
        """
        if not self.content_data:
            return []
        
        # Score each content
        scored_content = []
        for content in self.content_data:
            engagement_rate = 0.0
            if content.views > 0:
                total_engagements = content.likes + content.comments + content.shares
                engagement_rate = total_engagements / content.views
            
            # Combined performance score
            score = (
                content.retention_rate * 0.35 +
                content.completion_rate * 0.35 +
                engagement_rate * 0.20 +
                content.ctr * 0.10
            )
            
            scored_content.append((content.content_id, score))
        
        # Sort by score
        scored_content.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N IDs
        top_ids = [content_id for content_id, _ in scored_content[:top_n]]
        
        logger.info(f"Identified {len(top_ids)} top performers")
        
        return top_ids
    
    # ========================================
    # Complete Analysis & Insights Generation
    # ========================================
    
    def generate_insights(self) -> MetricInsights:
        """
        Generate complete MetricInsights from all content data.
        
        This is the main output - comprehensive insights for brand rules.
        
        Returns:
            MetricInsights object
        """
        if len(self.content_data) < self.min_sample_size:
            raise ValueError(
                f"Insufficient data for insights: {len(self.content_data)} < {self.min_sample_size}"
            )
        
        insights_id = f"insights_{uuid.uuid4().hex[:12]}"
        
        # Run all analyses
        logger.info("Generating comprehensive metric insights...")
        
        engagement_metrics = self.analyze_engagement_metrics()
        retention_metrics = self.analyze_retention_metrics()
        ctr_metrics = self.analyze_ctr_metrics()
        
        best_scenes = self.analyze_scene_performance()
        best_colors = self.analyze_color_performance()
        best_formats = self.analyze_format_performance()
        
        correlations = self.calculate_aesthetic_performance_correlation()
        top_performers = self.identify_top_performers(top_n=10)
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level()
        
        # Build insights object
        insights = MetricInsights(
            insights_id=insights_id,
            best_performing_scenes=best_scenes,
            best_performing_colors=best_colors,
            best_content_formats=best_formats,
            aesthetic_performance_correlation=correlations,
            scene_engagement_correlation={},  # Could add more correlations
            color_retention_correlation={},
            avg_retention_rate=retention_metrics.get("avg_retention_rate", 0.0),
            avg_completion_rate=retention_metrics.get("avg_completion_rate", 0.0),
            avg_ctr=ctr_metrics.get("avg_ctr", 0.0),
            avg_engagement_rate=engagement_metrics.get("avg_engagement_rate", 0.0),
            top_performing_content=top_performers,
            sample_size=len(self.content_data),
            confidence_level=confidence,
        )
        
        logger.info(
            f"Generated insights {insights_id} from {len(self.content_data)} content pieces "
            f"(confidence: {confidence:.2f})"
        )
        
        return insights
    
    def _calculate_confidence_level(self) -> float:
        """
        Calculate statistical confidence based on sample size.
        
        Returns:
            Confidence level (0.0 to 1.0)
        """
        sample_size = len(self.content_data)
        
        # Simple confidence calculation based on sample size
        # More sophisticated approach could use actual statistical tests
        if sample_size < self.min_sample_size:
            return 0.0
        elif sample_size < 30:
            return 0.6
        elif sample_size < 50:
            return 0.75
        elif sample_size < 100:
            return 0.85
        else:
            return 0.95
    
    # ========================================
    # Utilities
    # ========================================
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of available data and readiness for analysis."""
        return {
            "total_content_pieces": len(self.content_data),
            "min_sample_size": self.min_sample_size,
            "ready_for_analysis": len(self.content_data) >= self.min_sample_size,
            "confidence_level": self._calculate_confidence_level(),
            "unique_scenes": len(set(c.dominant_scene for c in self.content_data if c.dominant_scene)),
            "date_range": self._get_date_range(),
        }
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get date range of content data."""
        if not self.content_data:
            return {"earliest": "", "latest": ""}
        
        dates = [c.published_at for c in self.content_data]
        return {
            "earliest": min(dates).isoformat(),
            "latest": max(dates).isoformat(),
        }
    
    def clear_data(self) -> None:
        """Clear all loaded content data."""
        self.content_data = []
        logger.info("Cleared all performance data")
