"""
Daily Learning Pipeline - Automated learning from real performance data

Runs daily to:
- Analyze content performance
- Detect retention patterns
- Update recommendations
- Produce learning reports
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging
import asyncio

from ..storage.model_metrics_store import ModelMetricsStore
from ..storage.metrics_aggregator import MetricsAggregator
from ..storage.schemas_metrics import (
    LearningReport,
    MetricType,
    MetricsReadRequest
)

logger = logging.getLogger(__name__)


class DailyLearningPipeline:
    """
    Daily learning pipeline that analyzes performance and produces insights.
    
    Runs automatically each day to learn from real content performance.
    """
    
    def __init__(
        self,
        metrics_store: ModelMetricsStore,
        aggregator: Optional[MetricsAggregator] = None
    ):
        """
        Initialize daily learning pipeline.
        
        Args:
            metrics_store: ModelMetricsStore instance
            aggregator: MetricsAggregator instance (optional)
        """
        self.metrics_store = metrics_store
        self.aggregator = aggregator or MetricsAggregator(metrics_store)
        logger.info("DailyLearningPipeline initialized")
    
    async def run_daily_learning(
        self,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Run complete daily learning cycle.
        
        Args:
            target_date: Date to analyze (default: yesterday)
            
        Returns:
            Results dict with report and insights
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"🧠 Starting daily learning for {target_date}")
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Produce learning report
            logger.info("Step 1: Producing learning report")
            report = await self.aggregator.produce_learning_report(target_date)
            
            # Step 2: Analyze retention patterns
            logger.info("Step 2: Analyzing retention patterns")
            retention_patterns = await self._analyze_retention_patterns(target_date)
            
            # Step 3: Discover content insights
            logger.info("Step 3: Discovering content insights")
            content_insights = await self._discover_content_insights(target_date)
            
            # Step 4: Generate recommendations
            logger.info("Step 4: Generating recommendations")
            recommendations = await self._generate_recommendations(
                report,
                retention_patterns,
                content_insights
            )
            
            # Step 5: Update learning state
            logger.info("Step 5: Updating learning state")
            learning_state = await self._update_learning_state(
                report,
                retention_patterns,
                recommendations
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Daily learning completed in {processing_time:.2f}s")
            
            return {
                "success": True,
                "target_date": target_date.isoformat(),
                "report": report,
                "retention_patterns": retention_patterns,
                "content_insights": content_insights,
                "recommendations": recommendations,
                "learning_state": learning_state,
                "processing_time_sec": processing_time
            }
            
        except Exception as e:
            logger.error(f"Daily learning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "target_date": target_date.isoformat()
            }
    
    async def _analyze_retention_patterns(
        self,
        target_date: date
    ) -> Dict[str, Any]:
        """Analyze retention patterns for the day."""
        request = MetricsReadRequest(
            metric_types=[MetricType.RETENTION],
            date_from=target_date,
            date_to=target_date,
            limit=1000
        )
        
        metrics = await self.metrics_store.read_metrics(request)
        retention_data = metrics["metrics"].get("retention", [])
        
        if not retention_data:
            return {
                "total_analyzed": 0,
                "patterns": []
            }
        
        # Analyze drop-off points
        drop_off_analysis = self._analyze_drop_off_points(retention_data)
        
        # Analyze completion rates
        completion_analysis = self._analyze_completion_rates(retention_data)
        
        # Identify best retention content
        best_retention = sorted(
            retention_data,
            key=lambda x: x.get("avg_watch_percentage", 0),
            reverse=True
        )[:10]
        
        return {
            "total_analyzed": len(retention_data),
            "avg_retention": sum(r.get("avg_watch_percentage", 0) for r in retention_data) / len(retention_data),
            "drop_off_analysis": drop_off_analysis,
            "completion_analysis": completion_analysis,
            "best_retention_ids": [r["content_id"] for r in best_retention],
            "patterns": [
                {
                    "type": "high_retention",
                    "count": len([r for r in retention_data if r.get("avg_watch_percentage", 0) >= 0.7]),
                    "description": "Content with ≥70% retention"
                },
                {
                    "type": "low_retention",
                    "count": len([r for r in retention_data if r.get("avg_watch_percentage", 0) < 0.4]),
                    "description": "Content with <40% retention (needs improvement)"
                }
            ]
        }
    
    def _analyze_drop_off_points(
        self,
        retention_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze common drop-off points."""
        # TODO: Implement sophisticated drop-off analysis
        # For now, simple analysis
        
        all_drop_offs = []
        for r in retention_data:
            drop_offs = r.get("drop_off_points")
            if drop_offs:
                import json
                if isinstance(drop_offs, str):
                    drop_offs = json.loads(drop_offs)
                all_drop_offs.extend(drop_offs)
        
        if not all_drop_offs:
            return {"common_drop_offs": []}
        
        # Find most common drop-off times
        from collections import Counter
        drop_off_counter = Counter(all_drop_offs)
        common_drop_offs = drop_off_counter.most_common(5)
        
        return {
            "common_drop_offs": [
                {"time_sec": time, "frequency": freq}
                for time, freq in common_drop_offs
            ],
            "insights": [
                f"Common drop-off at {time}s ({freq} occurrences)"
                for time, freq in common_drop_offs[:3]
            ]
        }
    
    def _analyze_completion_rates(
        self,
        retention_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze completion rates."""
        completion_rates = [
            r.get("completion_rate", 0)
            for r in retention_data
            if r.get("completion_rate") is not None
        ]
        
        if not completion_rates:
            return {"avg_completion": 0.0}
        
        import statistics
        
        return {
            "avg_completion": statistics.mean(completion_rates),
            "median_completion": statistics.median(completion_rates),
            "high_completion_count": len([c for c in completion_rates if c >= 0.7]),
            "low_completion_count": len([c for c in completion_rates if c < 0.3])
        }
    
    async def _discover_content_insights(
        self,
        target_date: date
    ) -> Dict[str, Any]:
        """Discover insights from content performance."""
        # Read engagement metrics
        request = MetricsReadRequest(
            metric_types=[MetricType.ENGAGEMENT],
            date_from=target_date,
            date_to=target_date,
            limit=1000
        )
        
        metrics = await self.metrics_store.read_metrics(request)
        engagement_data = metrics["metrics"].get("engagement", [])
        
        if not engagement_data:
            return {
                "total_analyzed": 0,
                "insights": []
            }
        
        import statistics
        
        # Analyze engagement patterns
        avg_engagement = statistics.mean([
            e.get("engagement_rate", 0) for e in engagement_data
        ])
        
        avg_save_rate = statistics.mean([
            e.get("save_rate", 0) for e in engagement_data
        ])
        
        # Identify viral content (high velocity)
        viral_content = [
            e for e in engagement_data
            if e.get("views_velocity", 0) >= 500
        ]
        
        # Platform performance
        platform_stats = {}
        for e in engagement_data:
            platform = e.get("platform")
            if platform:
                if platform not in platform_stats:
                    platform_stats[platform] = []
                platform_stats[platform].append(e.get("engagement_rate", 0))
        
        platform_insights = {
            platform: {
                "count": len(rates),
                "avg_engagement": statistics.mean(rates)
            }
            for platform, rates in platform_stats.items()
        }
        
        insights = []
        
        if avg_engagement >= 0.08:
            insights.append("✅ Strong engagement across content")
        elif avg_engagement < 0.03:
            insights.append("⚠️ Low engagement - review CTAs and hooks")
        
        if avg_save_rate >= 0.05:
            insights.append("📌 High save rate - content provides value")
        
        if viral_content:
            insights.append(f"🚀 {len(viral_content)} viral pieces detected")
        
        return {
            "total_analyzed": len(engagement_data),
            "avg_engagement": avg_engagement,
            "avg_save_rate": avg_save_rate,
            "viral_count": len(viral_content),
            "platform_insights": platform_insights,
            "insights": insights
        }
    
    async def _generate_recommendations(
        self,
        report: LearningReport,
        retention_patterns: Dict[str, Any],
        content_insights: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Retention-based recommendations
        avg_retention = retention_patterns.get("avg_retention", 0)
        if avg_retention < 0.4:
            recommendations.append(
                "🎯 PRIORITY: Improve content hooks - retention below 40%"
            )
        
        # Drop-off recommendations
        drop_off = retention_patterns.get("drop_off_analysis", {})
        common_drops = drop_off.get("common_drop_offs", [])
        if common_drops and common_drops[0]["time_sec"] < 3:
            recommendations.append(
                "⚡ Strengthen first 3 seconds - common early drop-off detected"
            )
        
        # Engagement recommendations
        avg_engagement = content_insights.get("avg_engagement", 0)
        if avg_engagement < 0.05:
            recommendations.append(
                "📢 Add stronger CTAs - engagement below 5%"
            )
        
        # Platform recommendations
        platform_insights = content_insights.get("platform_insights", {})
        for platform, stats in platform_insights.items():
            if stats["avg_engagement"] > 0.1:
                recommendations.append(
                    f"🚀 Scale {platform} - strong {stats['avg_engagement']:.1%} engagement"
                )
        
        # Viral content recommendations
        if content_insights.get("viral_count", 0) > 0:
            recommendations.append(
                "🔥 Analyze viral content patterns - replicate successful elements"
            )
        
        return recommendations
    
    async def _update_learning_state(
        self,
        report: LearningReport,
        retention_patterns: Dict[str, Any],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """Update persistent learning state."""
        # TODO: Implement persistent learning state storage
        # This would update:
        # - Rules Engine thresholds
        # - Content Engine preferences
        # - Satellite Engine scheduling
        # - Brand Engine drift detection
        
        return {
            "updated_at": datetime.utcnow().isoformat(),
            "report_id": report.report_id,
            "recommendations_count": len(recommendations),
            "avg_retention": retention_patterns.get("avg_retention", 0),
            "brand_alignment": report.brand_alignment_score
        }
    
    async def get_learning_history(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get learning history for the past N days."""
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)
        
        snapshots = await self.metrics_store.read_daily_snapshots(
            start_date=start_date,
            end_date=end_date
        )
        
        return [
            {
                "date": snap.snapshot_date.isoformat(),
                "content_analyzed": snap.total_content_analyzed,
                "avg_retention": snap.avg_retention,
                "avg_engagement": snap.avg_engagement_rate,
                "insights_count": len(snap.insights),
                "recommendations_count": len(snap.recommendations)
            }
            for snap in snapshots
        ]
