"""
Best Time to Post - Analyze optimal posting times based on historical performance
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from collections import defaultdict
import logging
import statistics

from ..storage.model_metrics_store import ModelMetricsStore
from ..storage.schemas_metrics import BestTimeToPost, Platform, ChannelType, MetricsReadRequest, MetricType

logger = logging.getLogger(__name__)


class BestTimeToPostAnalyzer:
    """Analyze optimal posting times per platform."""
    
    def __init__(self, metrics_store: ModelMetricsStore):
        self.metrics_store = metrics_store
        logger.info("BestTimeToPostAnalyzer initialized")
    
    async def analyze_best_times(
        self,
        platform: Platform,
        channel_type: ChannelType = ChannelType.OFFICIAL,
        days_back: int = 30
    ) -> BestTimeToPost:
        """
        Analyze best posting times.
        
        Args:
            platform: Platform to analyze
            channel_type: Channel type
            days_back: Days of history to analyze
            
        Returns:
            BestTimeToPost with recommendations
        """
        # Read historical engagement data
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        request = MetricsReadRequest(
            metric_types=[MetricType.ENGAGEMENT],
            platform=platform,
            channel_type=channel_type,
            date_from=start_date,
            date_to=end_date,
            limit=1000
        )
        
        metrics = await self.metrics_store.read_metrics(request)
        engagement_data = metrics["metrics"].get("engagement", [])
        
        if not engagement_data:
            # Return defaults
            return BestTimeToPost(
                platform=platform,
                channel_type=channel_type,
                best_hours=[7, 12, 18],
                best_days=["Monday", "Wednesday", "Friday"],
                hourly_performance={},
                daily_performance={},
                confidence=0.1,
                sample_size=0
            )
        
        # Analyze by hour and day
        hourly_stats = defaultdict(list)
        daily_stats = defaultdict(list)
        
        for e in engagement_data:
            # Parse timestamp
            measured_at = e.get("measured_at")
            if measured_at:
                dt = datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
                hour = dt.hour
                day = dt.strftime("%A")
                
                engagement_rate = e.get("engagement_rate", 0)
                hourly_stats[hour].append(engagement_rate)
                daily_stats[day].append(engagement_rate)
        
        # Calculate averages
        hourly_performance = {
            hour: statistics.mean(rates)
            for hour, rates in hourly_stats.items()
        }
        
        daily_performance = {
            day: statistics.mean(rates)
            for day, rates in daily_stats.items()
        }
        
        # Find best hours (top 3)
        sorted_hours = sorted(hourly_performance.items(), key=lambda x: x[1], reverse=True)
        best_hours = [hour for hour, _ in sorted_hours[:3]]
        
        # Find best days (top 3)
        sorted_days = sorted(daily_performance.items(), key=lambda x: x[1], reverse=True)
        best_days = [day for day, _ in sorted_days[:3]]
        
        # Calculate confidence
        confidence = min(0.95, len(engagement_data) / 100)
        
        return BestTimeToPost(
            platform=platform,
            channel_type=channel_type,
            best_hours=best_hours,
            best_days=best_days,
            hourly_performance=hourly_performance,
            daily_performance=daily_performance,
            confidence=confidence,
            sample_size=len(engagement_data)
        )
