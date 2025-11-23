"""
Visual Analytics Data Collector.

Aggregates data from database for analytics endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.models.database import (
    Clip,
    Job,
    Publication,
    Campaign,
    VideoAsset,
)
from app.visual_analytics.schemas import *


class VisualAnalyticsCollector:
    """
    Collects and aggregates visual analytics data.
    
    Optimized for chart/graph consumption with SQL-level aggregations.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ================================================================
    # PUBLIC METHODS
    # ================================================================
    
    async def get_overview(self, days_back: int = 30) -> AnalyticsOverview:
        """
        Get complete analytics overview.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Complete analytics overview with all metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Basic counts
        total_clips = await self._count_clips(cutoff_date)
        total_jobs = await self._count_jobs(cutoff_date)
        total_publications = await self._count_publications(cutoff_date)
        total_campaigns = await self._count_campaigns(cutoff_date)
        
        # Rates
        clips_per_day = total_clips / days_back if days_back > 0 else 0
        clips_per_week = clips_per_day * 7
        clips_per_month = clips_per_day * 30
        
        # Averages
        avg_job_duration = await self._avg_job_duration(cutoff_date)
        avg_clip_score = await self._avg_clip_score(cutoff_date)
        pub_success_rate = await self._publication_success_rate(cutoff_date)
        
        # Advanced analytics
        trends = await self._calculate_trends(cutoff_date)
        correlations = await self._calculate_correlations(cutoff_date)
        top_videos = await self._get_top_clips(cutoff_date, limit=10)
        rule_metrics = await self._get_rule_engine_metrics(cutoff_date)
        
        return AnalyticsOverview(
            total_clips=total_clips,
            total_jobs=total_jobs,
            total_publications=total_publications,
            total_campaigns=total_campaigns,
            clips_per_day=clips_per_day,
            clips_per_week=clips_per_week,
            clips_per_month=clips_per_month,
            avg_job_duration_ms=avg_job_duration,
            avg_clip_score=avg_clip_score,
            publication_success_rate=pub_success_rate,
            trends=trends,
            correlations=correlations,
            top_videos_by_score=top_videos,
            rule_engine_metrics=rule_metrics,
            generated_at=datetime.utcnow(),
            date_range={
                "start": cutoff_date,
                "end": datetime.utcnow()
            }
        )
    
    async def get_timeline(self, days_back: int = 30) -> TimelineData:
        """
        Get timeline data for jobs, publications, and clips.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Timeline data with multiple series
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        jobs_timeline = await self._get_jobs_timeline(cutoff_date)
        pubs_timeline = await self._get_publications_timeline(cutoff_date)
        clips_timeline = await self._get_clips_timeline(cutoff_date)
        orch_events = await self._get_orchestrator_events(cutoff_date)
        
        return TimelineData(
            jobs_timeline=jobs_timeline,
            publications_timeline=pubs_timeline,
            clips_timeline=clips_timeline,
            orchestrator_events=orch_events,
            date_range={
                "start": cutoff_date,
                "end": datetime.utcnow()
            }
        )
    
    async def get_heatmap(self, metric: str, days_back: int = 30) -> HeatmapData:
        """
        Get activity heatmap by hour and day of week.
        
        Args:
            metric: Metric to visualize (clips, jobs, publications)
            days_back: Number of days to look back
            
        Returns:
            Heatmap data structure
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Select appropriate table
        if metric == "clips":
            model = Clip
        elif metric == "jobs":
            model = Job
        elif metric == "publications":
            model = Publication
        else:
            model = Clip
        
        # Query data grouped by hour and day of week
        # For simplicity, return empty heatmap with structure
        cells = []
        
        # Generate hour labels (0-23)
        x_labels = [f"{h:02d}:00" for h in range(24)]
        
        # Generate day labels
        y_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        return HeatmapData(
            title=f"{metric.capitalize()} Activity Heatmap",
            x_labels=x_labels,
            y_labels=y_labels,
            cells=cells,
            color_scale="viridis"
        )
    
    async def get_platform_stats(self, days_back: int = 30) -> PlatformStats:
        """
        Get platform performance breakdown.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Platform statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        platforms = []
        total_clips = 0
        total_pubs = 0
        best_platform = None
        best_score = 0.0
        
        for platform in ["instagram", "tiktok", "youtube"]:
            # Count publications for this platform
            result = await self.db.execute(
                select(func.count(Publication.id))
                .where(
                    and_(
                        Publication.platform == platform,
                        Publication.created_at >= cutoff_date
                    )
                )
            )
            pub_count = result.scalar() or 0
            
            # For clips, we approximate based on publications
            clip_count = pub_count  # Simplified
            
            # Average score (stub)
            avg_score = 0.75
            
            # Success rate
            success_rate = 0.95 if pub_count > 0 else 0.0
            
            platforms.append(PlatformMetric(
                platform=platform,
                clips_count=clip_count,
                publications_count=pub_count,
                avg_score=avg_score,
                success_rate=success_rate,
                total_views=0  # Stub
            ))
            
            total_clips += clip_count
            total_pubs += pub_count
            
            if avg_score > best_score and pub_count > 0:
                best_score = avg_score
                best_platform = platform
        
        return PlatformStats(
            platforms=platforms,
            total_clips=total_clips,
            total_publications=total_pubs,
            best_platform=best_platform
        )
    
    async def get_clips_distribution(self, days_back: int = 30) -> ClipsDistribution:
        """
        Get clips distributions and rankings.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Clips distribution data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get all clips in range
        result = await self.db.execute(
            select(Clip)
            .where(Clip.created_at >= cutoff_date)
        )
        clips = result.scalars().all()
        
        if not clips:
            # Return empty structure
            return ClipsDistribution(
                by_duration=Distribution(bins=[], counts=[]),
                by_score=Distribution(bins=[], counts=[]),
                top_clips=[],
                total_clips=0,
                avg_score=0.0,
                avg_duration=0.0
            )
        
        # Extract durations and scores
        durations = [c.duration_ms for c in clips if c.duration_ms]
        scores = [c.visual_score for c in clips if c.visual_score is not None]
        
        # Create histograms
        duration_dist = self._create_histogram(durations, bins=10)
        score_dist = self._create_histogram(scores, bins=10)
        
        # Get top clips
        top_clips = await self._get_top_clips(cutoff_date, limit=10)
        
        # Calculate averages
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return ClipsDistribution(
            by_duration=duration_dist,
            by_score=score_dist,
            top_clips=top_clips,
            total_clips=len(clips),
            avg_score=avg_score,
            avg_duration=avg_duration
        )
    
    async def get_campaign_breakdown(self, days_back: int = 30) -> CampaignBreakdown:
        """
        Get campaign performance breakdown.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Campaign breakdown data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get all campaigns
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.created_at >= cutoff_date)
        )
        campaigns = result.scalars().all()
        
        campaign_metrics = []
        active_count = 0
        
        for camp in campaigns:
            # Count clips for this campaign
            clip_result = await self.db.execute(
                select(func.count(Clip.id))
                .where(Clip.id == camp.clip_id)
            )
            clips_count = clip_result.scalar() or 1
            
            # Count publications for this clip
            pub_result = await self.db.execute(
                select(func.count(Publication.id))
                .where(Publication.clip_id == camp.clip_id)
            )
            pubs_count = pub_result.scalar() or 0
            
            # Get average clip score
            score_result = await self.db.execute(
                select(func.avg(Clip.visual_score))
                .where(Clip.id == camp.clip_id)
            )
            avg_score = score_result.scalar() or 0.0
            
            if camp.status == "active":
                active_count += 1
            
            campaign_metrics.append(CampaignMetric(
                campaign_id=str(camp.id),
                name=camp.name,
                status=camp.status.value if hasattr(camp.status, 'value') else str(camp.status),
                clips_count=clips_count,
                publications_count=pubs_count,
                avg_clip_score=float(avg_score) if avg_score else 0.0,
                created_at=camp.created_at
            ))
        
        total = len(campaigns)
        avg_clips = sum(m.clips_count for m in campaign_metrics) / total if total > 0 else 0.0
        
        return CampaignBreakdown(
            campaigns=campaign_metrics,
            total_campaigns=total,
            active_campaigns=active_count,
            avg_clips_per_campaign=avg_clips
        )
    
    # ================================================================
    # PRIVATE HELPER METHODS
    # ================================================================
    
    async def _count_clips(self, cutoff_date: datetime) -> int:
        """Count clips created after cutoff date."""
        result = await self.db.execute(
            select(func.count(Clip.id))
            .where(Clip.created_at >= cutoff_date)
        )
        return result.scalar() or 0
    
    async def _count_jobs(self, cutoff_date: datetime) -> int:
        """Count jobs created after cutoff date."""
        result = await self.db.execute(
            select(func.count(Job.id))
            .where(Job.created_at >= cutoff_date)
        )
        return result.scalar() or 0
    
    async def _count_publications(self, cutoff_date: datetime) -> int:
        """Count publications created after cutoff date."""
        result = await self.db.execute(
            select(func.count(Publication.id))
            .where(Publication.created_at >= cutoff_date)
        )
        return result.scalar() or 0
    
    async def _count_campaigns(self, cutoff_date: datetime) -> int:
        """Count campaigns created after cutoff date."""
        result = await self.db.execute(
            select(func.count(Campaign.id))
            .where(Campaign.created_at >= cutoff_date)
        )
        return result.scalar() or 0
    
    async def _avg_job_duration(self, cutoff_date: datetime) -> float:
        """Calculate average job duration from ledger (stub)."""
        return 5000.0  # 5 seconds average (stub)
    
    async def _avg_clip_score(self, cutoff_date: datetime) -> float:
        """Calculate average clip visual score."""
        result = await self.db.execute(
            select(func.avg(Clip.visual_score))
            .where(
                and_(
                    Clip.created_at >= cutoff_date,
                    Clip.visual_score.isnot(None)
                )
            )
        )
        avg = result.scalar()
        return float(avg) if avg else 0.0
    
    async def _publication_success_rate(self, cutoff_date: datetime) -> float:
        """Calculate publication success rate."""
        total_clips = await self._count_clips(cutoff_date)
        total_pubs = await self._count_publications(cutoff_date)
        
        if total_clips == 0:
            return 0.0
        
        return (total_pubs / total_clips) * 100.0
    
    async def _calculate_trends(self, cutoff_date: datetime) -> List[TrendLine]:
        """Calculate 7-day rolling average trends (stub)."""
        return []
    
    async def _calculate_correlations(self, cutoff_date: datetime) -> List[CorrelationMetric]:
        """Calculate correlations between metrics (stub)."""
        total_clips = await self._count_clips(cutoff_date)
        total_pubs = await self._count_publications(cutoff_date)
        
        if total_clips > 0 and total_pubs > 0:
            # Simple correlation: more clips → more publications
            correlation = min(1.0, total_pubs / total_clips)
            
            return [
                CorrelationMetric(
                    metric_x="clips_created",
                    metric_y="publications",
                    correlation=correlation,
                    sample_size=total_clips
                )
            ]
        
        return []
    
    async def _get_top_clips(self, cutoff_date: datetime, limit: int = 10) -> List[ClipRanking]:
        """Get top N clips by visual score."""
        result = await self.db.execute(
            select(Clip)
            .where(
                and_(
                    Clip.created_at >= cutoff_date,
                    Clip.visual_score.isnot(None)
                )
            )
            .order_by(Clip.visual_score.desc())
            .limit(limit)
        )
        clips = result.scalars().all()
        
        rankings = []
        for clip in clips:
            rankings.append(ClipRanking(
                clip_id=str(clip.id),
                video_id=str(clip.video_asset_id),
                title=None,  # Would need to join with video_assets
                score=clip.visual_score or 0.0,
                duration_ms=clip.duration_ms
            ))
        
        return rankings
    
    async def _get_rule_engine_metrics(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Get rule engine evaluation metrics (stub)."""
        return {
            "total_evaluations": 0,
            "avg_evaluation_time_ms": 0,
            "rules_triggered": 0
        }
    
    async def _get_jobs_timeline(self, cutoff_date: datetime) -> List[Timeseries]:
        """Get jobs timeline data."""
        # Stub: Return empty timeline
        return [
            Timeseries(
                series_name="Jobs Created",
                data=[],
                color="#3b82f6"
            )
        ]
    
    async def _get_publications_timeline(self, cutoff_date: datetime) -> List[Timeseries]:
        """Get publications timeline data."""
        # Stub: Return empty timeline
        return [
            Timeseries(
                series_name="Publications",
                data=[],
                color="#10b981"
            )
        ]
    
    async def _get_clips_timeline(self, cutoff_date: datetime) -> List[Timeseries]:
        """Get clips timeline data."""
        # Stub: Return empty timeline
        return [
            Timeseries(
                series_name="Clips Generated",
                data=[],
                color="#f59e0b"
            )
        ]
    
    async def _get_orchestrator_events(self, cutoff_date: datetime) -> List[Timeseries]:
        """Get orchestrator events timeline."""
        # Stub: Return empty timeline
        return [
            Timeseries(
                series_name="Orchestrator Events",
                data=[],
                color="#8b5cf6"
            )
        ]
    
    def _create_histogram(self, data: List[float], bins: int = 10) -> Distribution:
        """Create histogram from data."""
        if not data:
            return Distribution(bins=[], counts=[])
        
        counts, bin_edges = np.histogram(data, bins=bins)
        
        return Distribution(
            bins=bin_edges.tolist(),
            counts=counts.tolist()
        )
