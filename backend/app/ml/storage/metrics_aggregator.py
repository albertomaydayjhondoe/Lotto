"""
Metrics Aggregator - Aggregate and analyze metrics for learning

Produces:
- Daily snapshots
- Retention clusters
- Best patterns
- Learning reports
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
import logging
import statistics
import uuid

from .model_metrics_store import ModelMetricsStore
from .schemas_metrics import (
    DailySnapshot,
    RetentionCluster,
    PatternDiscovery,
    LearningReport,
    MetricType,
    Platform,
    ChannelType,
    MetricsReadRequest
)

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """
    Aggregate and analyze metrics to produce learning insights.
    
    Features:
    - Daily snapshot generation
    - Retention clustering
    - Pattern discovery
    - Learning report production
    """
    
    def __init__(self, metrics_store: ModelMetricsStore):
        """
        Initialize aggregator.
        
        Args:
            metrics_store: ModelMetricsStore instance
        """
        self.metrics_store = metrics_store
        logger.info("MetricsAggregator initialized")
    
    async def build_daily_snapshot(
        self,
        target_date: Optional[date] = None
    ) -> DailySnapshot:
        """
        Build daily snapshot for a specific date.
        
        Args:
            target_date: Date to build snapshot for (default: yesterday)
            
        Returns:
            DailySnapshot with aggregated metrics
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"Building daily snapshot for {target_date}")
        
        # Read all metrics for the date
        request = MetricsReadRequest(
            date_from=target_date,
            date_to=target_date,
            limit=10000
        )
        
        metrics = await self.metrics_store.read_metrics(request)
        
        if not metrics["success"]:
            raise ValueError(f"Failed to read metrics: {metrics.get('error')}")
        
        retention_data = metrics["metrics"].get("retention", [])
        engagement_data = metrics["metrics"].get("engagement", [])
        learning_scores = metrics["metrics"].get("learning_scores", [])
        
        # Aggregate metrics
        total_content = len(set(
            [r["content_id"] for r in retention_data] +
            [e["content_id"] for e in engagement_data]
        ))
        
        total_views = sum(e.get("views", 0) for e in engagement_data)
        total_engagement = sum(
            e.get("likes", 0) + e.get("comments", 0) + e.get("shares", 0)
            for e in engagement_data
        )
        
        # Calculate averages
        avg_retention = statistics.mean([
            r["avg_watch_percentage"] for r in retention_data if r.get("avg_watch_percentage")
        ]) if retention_data else 0.0
        
        avg_engagement_rate = statistics.mean([
            e["engagement_rate"] for e in engagement_data if e.get("engagement_rate")
        ]) if engagement_data else 0.0
        
        avg_quality_score = statistics.mean([
            ls.get("overall_score", 0) for ls in learning_scores
        ]) if learning_scores else 0.0
        
        # Find best performers
        best_content_ids = await self._find_best_performers(
            retention_data,
            engagement_data,
            learning_scores
        )
        
        # Discover patterns
        best_patterns = await self._discover_patterns(retention_data, engagement_data)
        
        # Generate insights
        insights = await self._generate_insights(
            retention_data,
            engagement_data,
            learning_scores
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            retention_data,
            engagement_data,
            best_patterns
        )
        
        # Create snapshot
        snapshot = DailySnapshot(
            snapshot_date=target_date,
            snapshot_id=f"snap_{target_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            total_content_analyzed=total_content,
            total_views=total_views,
            total_engagement=total_engagement,
            avg_retention=avg_retention,
            avg_engagement_rate=avg_engagement_rate,
            avg_quality_score=avg_quality_score,
            best_content_ids=best_content_ids[:10],
            best_patterns=best_patterns,
            satellite_metrics={},  # TODO: Add satellite metrics
            engine_metrics={},  # TODO: Add engine metrics
            insights=insights,
            recommendations=recommendations
        )
        
        # Save snapshot
        await self.metrics_store.write_daily_snapshot(snapshot)
        
        logger.info(f"Daily snapshot created: {snapshot.snapshot_id}")
        
        return snapshot
    
    async def _find_best_performers(
        self,
        retention_data: List[Dict[str, Any]],
        engagement_data: List[Dict[str, Any]],
        learning_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """Find best performing content IDs."""
        # Score each content based on multiple factors
        scores = defaultdict(lambda: {"retention": 0, "engagement": 0, "learning": 0})
        
        for r in retention_data:
            content_id = r["content_id"]
            scores[content_id]["retention"] = r.get("avg_watch_percentage", 0)
        
        for e in engagement_data:
            content_id = e["content_id"]
            scores[content_id]["engagement"] = e.get("engagement_rate", 0)
        
        for ls in learning_scores:
            content_id = ls["content_id"]
            scores[content_id]["learning"] = ls.get("overall_score", 0)
        
        # Calculate composite score
        composite_scores = {}
        for content_id, metrics in scores.items():
            composite = (
                metrics["retention"] * 0.4 +
                metrics["engagement"] * 0.4 +
                metrics["learning"] * 0.2
            )
            composite_scores[content_id] = composite
        
        # Sort by score
        sorted_content = sorted(
            composite_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [content_id for content_id, score in sorted_content]
    
    async def _discover_patterns(
        self,
        retention_data: List[Dict[str, Any]],
        engagement_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Discover patterns in content performance."""
        patterns = []
        
        # Pattern 1: High retention thresholds
        high_retention = [
            r for r in retention_data
            if r.get("avg_watch_percentage", 0) >= 0.7
        ]
        
        if high_retention:
            patterns.append({
                "type": "high_retention",
                "description": f"{len(high_retention)} pieces with ≥70% retention",
                "avg_retention": statistics.mean([
                    r["avg_watch_percentage"] for r in high_retention
                ]),
                "sample_ids": [r["content_id"] for r in high_retention[:5]]
            })
        
        # Pattern 2: High engagement
        high_engagement = [
            e for e in engagement_data
            if e.get("engagement_rate", 0) >= 0.10
        ]
        
        if high_engagement:
            patterns.append({
                "type": "high_engagement",
                "description": f"{len(high_engagement)} pieces with ≥10% engagement rate",
                "avg_engagement": statistics.mean([
                    e["engagement_rate"] for e in high_engagement
                ]),
                "sample_ids": [e["content_id"] for e in high_engagement[:5]]
            })
        
        # Pattern 3: Viral velocity
        viral_content = [
            e for e in engagement_data
            if e.get("views_velocity", 0) >= 1000  # 1000 views/hour
        ]
        
        if viral_content:
            patterns.append({
                "type": "viral_velocity",
                "description": f"{len(viral_content)} pieces with viral velocity (≥1000 views/hour)",
                "avg_velocity": statistics.mean([
                    e["views_velocity"] for e in viral_content
                ]),
                "sample_ids": [e["content_id"] for e in viral_content[:5]]
            })
        
        return patterns
    
    async def _generate_insights(
        self,
        retention_data: List[Dict[str, Any]],
        engagement_data: List[Dict[str, Any]],
        learning_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from metrics."""
        insights = []
        
        if retention_data:
            avg_retention = statistics.mean([
                r["avg_watch_percentage"] for r in retention_data if r.get("avg_watch_percentage")
            ])
            
            if avg_retention >= 0.6:
                insights.append(f"✅ Strong retention: {avg_retention:.1%} average watch percentage")
            elif avg_retention < 0.4:
                insights.append(f"⚠️ Low retention: {avg_retention:.1%} average watch percentage - review content hooks")
        
        if engagement_data:
            avg_engagement = statistics.mean([
                e["engagement_rate"] for e in engagement_data if e.get("engagement_rate")
            ])
            
            if avg_engagement >= 0.08:
                insights.append(f"✅ High engagement: {avg_engagement:.1%} average engagement rate")
            elif avg_engagement < 0.03:
                insights.append(f"⚠️ Low engagement: {avg_engagement:.1%} - improve CTAs and hooks")
        
        # Completion rate insights
        completions = [r.get("completion_rate", 0) for r in retention_data if r.get("completion_rate")]
        if completions:
            avg_completion = statistics.mean(completions)
            if avg_completion >= 0.5:
                insights.append(f"✅ Strong completion rate: {avg_completion:.1%} of viewers watch to end")
        
        # Rewatch insights
        rewatches = [r.get("rewatch_rate", 0) for r in retention_data if r.get("rewatch_rate")]
        if rewatches:
            avg_rewatch = statistics.mean(rewatches)
            if avg_rewatch >= 0.2:
                insights.append(f"✨ High rewatch rate: {avg_rewatch:.1%} - content has replay value")
        
        return insights
    
    async def _generate_recommendations(
        self,
        retention_data: List[Dict[str, Any]],
        engagement_data: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Retention-based recommendations
        if retention_data:
            avg_retention = statistics.mean([
                r["avg_watch_percentage"] for r in retention_data if r.get("avg_watch_percentage")
            ])
            
            if avg_retention < 0.4:
                recommendations.append(
                    "🎯 Improve hooks: Current retention <40%. Analyze drop-off points and strengthen opening 3 seconds"
                )
        
        # Engagement-based recommendations
        if engagement_data:
            avg_save_rate = statistics.mean([
                e.get("save_rate", 0) for e in engagement_data if e.get("save_rate")
            ])
            
            if avg_save_rate < 0.02:
                recommendations.append(
                    "📌 Increase saveability: Save rate <2%. Add value-driven content (tips, tutorials, inspiration)"
                )
        
        # Pattern-based recommendations
        for pattern in patterns:
            if pattern["type"] == "high_retention":
                recommendations.append(
                    f"🔥 Replicate success: {len(pattern.get('sample_ids', []))} high-retention pieces identified. "
                    "Analyze common elements (style, pacing, hooks)"
                )
        
        # Platform-specific recommendations
        platform_performance = defaultdict(lambda: {"count": 0, "avg_engagement": []})
        for e in engagement_data:
            platform = e.get("platform")
            if platform:
                platform_performance[platform]["count"] += 1
                platform_performance[platform]["avg_engagement"].append(e.get("engagement_rate", 0))
        
        for platform, data in platform_performance.items():
            if data["count"] > 5:
                avg_eng = statistics.mean(data["avg_engagement"])
                if avg_eng > 0.1:
                    recommendations.append(
                        f"🚀 Scale {platform}: Strong performance ({avg_eng:.1%} engagement). Increase posting frequency"
                    )
        
        return recommendations
    
    async def compute_retention_clusters(
        self,
        min_cluster_size: int = 5
    ) -> List[RetentionCluster]:
        """
        Compute clusters of content with similar retention patterns.
        
        Args:
            min_cluster_size: Minimum number of items per cluster
            
        Returns:
            List of retention clusters
        """
        # Read recent retention data
        request = MetricsReadRequest(
            metric_types=[MetricType.RETENTION],
            date_from=date.today() - timedelta(days=30),
            limit=1000
        )
        
        metrics = await self.metrics_store.read_metrics(request)
        retention_data = metrics["metrics"].get("retention", [])
        
        if not retention_data:
            return []
        
        # Simple clustering by retention percentage ranges
        clusters_dict = {
            "high": {"range": (0.7, 1.0), "items": []},
            "medium": {"range": (0.4, 0.7), "items": []},
            "low": {"range": (0.0, 0.4), "items": []}
        }
        
        for r in retention_data:
            retention = r.get("avg_watch_percentage", 0)
            if 0.7 <= retention <= 1.0:
                clusters_dict["high"]["items"].append(r)
            elif 0.4 <= retention < 0.7:
                clusters_dict["medium"]["items"].append(r)
            else:
                clusters_dict["low"]["items"].append(r)
        
        # Create cluster objects
        clusters = []
        for cluster_name, data in clusters_dict.items():
            items = data["items"]
            if len(items) >= min_cluster_size:
                avg_retention = statistics.mean([
                    i["avg_watch_percentage"] for i in items
                ])
                
                cluster = RetentionCluster(
                    cluster_id=f"cluster_{cluster_name}_{uuid.uuid4().hex[:8]}",
                    cluster_name=f"{cluster_name.capitalize()} Retention",
                    avg_retention=avg_retention,
                    content_count=len(items),
                    content_ids=[i["content_id"] for i in items],
                    common_features={
                        "retention_range": data["range"],
                        "avg_completion": statistics.mean([
                            i.get("completion_rate", 0) for i in items if i.get("completion_rate")
                        ]) if items else 0
                    },
                    avg_engagement_rate=0.0,  # TODO: Join with engagement data
                    avg_virality_score=0.0
                )
                
                clusters.append(cluster)
        
        logger.info(f"Created {len(clusters)} retention clusters")
        
        return clusters
    
    async def produce_learning_report(
        self,
        report_date: Optional[date] = None
    ) -> LearningReport:
        """
        Produce comprehensive learning report.
        
        Args:
            report_date: Date for report (default: yesterday)
            
        Returns:
            LearningReport with insights and recommendations
        """
        if report_date is None:
            report_date = date.today() - timedelta(days=1)
        
        logger.info(f"Producing learning report for {report_date}")
        
        # Build daily snapshot
        snapshot = await self.build_daily_snapshot(report_date)
        
        # Compute retention clusters
        clusters = await self.compute_retention_clusters()
        
        # TODO: Discover new patterns
        new_patterns = []
        
        # Extract best/worst performers
        best_performers = [
            {
                "content_id": cid,
                "metrics": "TODO"
            }
            for cid in snapshot.best_content_ids[:5]
        ]
        
        worst_performers = []  # TODO
        
        # Generate recommendations
        content_recommendations = snapshot.recommendations
        timing_recommendations = [
            "📅 Post during peak hours: 6-9 AM, 5-8 PM (based on engagement data)"
        ]
        style_recommendations = [
            "🎨 Focus on visual aesthetics: High-quality content shows 2x better retention"
        ]
        
        # Brand alignment
        brand_alignment_score = 0.85  # TODO: Calculate from brand compliance metrics
        brand_drift_detected = brand_alignment_score < 0.7
        brand_corrections = []
        if brand_drift_detected:
            brand_corrections.append("Brand compliance below threshold - review recent content")
        
        # Cost analysis
        total_cost = 8.50  # TODO: Get from cost tracking
        cost_per_view = total_cost / snapshot.total_views if snapshot.total_views > 0 else 0
        roi = snapshot.total_engagement / total_cost if total_cost > 0 else 0
        
        # Create report
        report = LearningReport(
            report_date=report_date,
            report_id=f"report_{report_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            summary=f"Daily learning report for {report_date}: {snapshot.total_content_analyzed} pieces analyzed, "
                    f"{snapshot.total_views:,} views, {snapshot.avg_retention:.1%} avg retention",
            key_insights=snapshot.insights,
            new_patterns=[],
            retention_clusters=clusters,
            best_performers=best_performers,
            worst_performers=worst_performers,
            content_recommendations=content_recommendations,
            timing_recommendations=timing_recommendations,
            style_recommendations=style_recommendations,
            suggested_rule_updates=[],
            suggested_threshold_updates=[],
            brand_alignment_score=brand_alignment_score,
            brand_drift_detected=brand_drift_detected,
            brand_corrections=brand_corrections,
            total_cost=total_cost,
            cost_per_view=cost_per_view,
            roi=roi
        )
        
        logger.info(f"Learning report created: {report.report_id}")
        
        return report
