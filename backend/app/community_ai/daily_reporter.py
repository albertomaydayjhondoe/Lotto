"""
Daily Reporter - Automated Reporting System for Community Manager AI

Generates daily performance reports with metrics, insights, and recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from .models import (
    DailyReport,
    PerformanceMetric
)

logger = logging.getLogger(__name__)


class DailyReporter:
    """
    Daily automated reporting system.
    
    Generates comprehensive daily reports with:
    - Publications summary
    - Performance metrics
    - Audience changes
    - Alerts
    - Strategic recommendations
    - Tomorrow's focus areas
    """
    
    def __init__(self, mode: str = "live"):
        """
        Initialize reporter.
        
        Args:
            mode: "live" or "stub"
        """
        self.mode = mode
    
    def generate_daily_report(
        self,
        user_id: str,
        date: datetime,
        publications_data: Optional[Dict[str, Any]] = None,
        performance_data: Optional[Dict[str, Any]] = None,
        audience_data: Optional[Dict[str, Any]] = None
    ) -> DailyReport:
        """
        Generate daily report.
        
        Args:
            user_id: Artist user ID
            date: Report date
            publications_data: Data about posts published today
            performance_data: Performance metrics data
            audience_data: Audience growth/engagement data
        
        Returns:
            Complete daily report
        """
        logger.info(f"📋 Generating daily report for {date.date()}")
        
        if self.mode == "stub":
            return self._generate_stub_report(user_id, date)
        
        # Extract publications summary
        posts_published = publications_data.get("total_posts", 0) if publications_data else 0
        official_posts = publications_data.get("official_count", 0) if publications_data else 0
        satellite_posts = publications_data.get("satellite_count", 0) if publications_data else 0
        
        # Extract performance metrics
        total_views = performance_data.get("total_views", 0) if performance_data else 0
        total_engagement = performance_data.get("total_engagement", 0) if performance_data else 0
        avg_retention = performance_data.get("avg_retention", 0.0) if performance_data else 0.0
        avg_ctr = performance_data.get("avg_ctr", 0.0) if performance_data else 0.0
        
        # Build metrics with trends
        metrics = self._build_metrics(performance_data)
        
        # Identify top/worst performers
        best_post_id = None
        best_post_reason = None
        worst_post_id = None
        worst_post_reason = None
        
        if performance_data and "posts" in performance_data:
            posts = performance_data["posts"]
            if posts:
                best_post = max(posts, key=lambda p: p.get("retention", 0))
                best_post_id = best_post["id"]
                best_post_reason = f"{best_post.get('retention', 0)*100:.1f}% retention"
                
                worst_post = min(posts, key=lambda p: p.get("retention", 1))
                worst_post_id = worst_post["id"]
                worst_post_reason = f"{worst_post.get('retention', 0)*100:.1f}% retention"
        
        # Extract audience changes
        followers_change = audience_data.get("followers_change", 0) if audience_data else 0
        audience_growth_rate = audience_data.get("growth_rate", 0.0) if audience_data else 0.0
        
        # Generate alerts
        alerts = self._generate_alerts(
            performance_data,
            audience_data,
            metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics,
            alerts,
            performance_data
        )
        
        # Tomorrow's focus
        tomorrow_focus = self._generate_tomorrow_focus(
            metrics,
            alerts,
            recommendations
        )
        
        report = DailyReport(
            report_id=f"report_{user_id}_{date.strftime('%Y%m%d')}",
            date=date,
            user_id=user_id,
            posts_published=posts_published,
            official_posts=official_posts,
            satellite_posts=satellite_posts,
            total_views=total_views,
            total_engagement=total_engagement,
            avg_retention=avg_retention,
            avg_ctr=avg_ctr,
            metrics=metrics,
            best_post_id=best_post_id,
            best_post_reason=best_post_reason,
            worst_post_id=worst_post_id,
            worst_post_reason=worst_post_reason,
            followers_change=followers_change,
            audience_growth_rate=audience_growth_rate,
            alerts=alerts,
            recommendations=recommendations,
            tomorrow_focus=tomorrow_focus,
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"✅ Report generated: {posts_published} posts, {len(alerts)} alerts")
        return report
    
    def _build_metrics(self, performance_data: Optional[Dict[str, Any]]) -> List[PerformanceMetric]:
        """Build performance metrics with trends."""
        if not performance_data:
            return []
        
        metrics = []
        
        # Views metric
        if "total_views" in performance_data and "previous_views" in performance_data:
            current = performance_data["total_views"]
            previous = performance_data["previous_views"]
            change = ((current - previous) / previous * 100) if previous > 0 else 0
            trend = "up" if change > 5 else ("down" if change < -5 else "stable")
            
            metrics.append(PerformanceMetric(
                metric_name="Total Views",
                value=float(current),
                change_percentage=change,
                trend=trend
            ))
        
        # Retention metric
        if "avg_retention" in performance_data and "previous_retention" in performance_data:
            current = performance_data["avg_retention"]
            previous = performance_data["previous_retention"]
            change = ((current - previous) / previous * 100) if previous > 0 else 0
            trend = "up" if change > 2 else ("down" if change < -2 else "stable")
            
            metrics.append(PerformanceMetric(
                metric_name="Avg Retention",
                value=current,
                change_percentage=change,
                trend=trend
            ))
        
        # CTR metric
        if "avg_ctr" in performance_data and "previous_ctr" in performance_data:
            current = performance_data["avg_ctr"]
            previous = performance_data["previous_ctr"]
            change = ((current - previous) / previous * 100) if previous > 0 else 0
            trend = "up" if change > 5 else ("down" if change < -5 else "stable")
            
            metrics.append(PerformanceMetric(
                metric_name="Avg CTR",
                value=current,
                change_percentage=change,
                trend=trend
            ))
        
        return metrics
    
    def _generate_alerts(
        self,
        performance_data: Optional[Dict[str, Any]],
        audience_data: Optional[Dict[str, Any]],
        metrics: List[PerformanceMetric]
    ) -> List[str]:
        """Generate alerts."""
        alerts = []
        
        # Performance alerts
        for metric in metrics:
            if metric.trend == "down" and abs(metric.change_percentage) > 15:
                alerts.append(f"⚠️ {metric.metric_name} down {abs(metric.change_percentage):.1f}%")
        
        # Audience alerts
        if audience_data:
            followers_change = audience_data.get("followers_change", 0)
            if followers_change < 0:
                alerts.append(f"⚠️ Lost {abs(followers_change)} followers today")
        
        # Content alerts
        if performance_data:
            posts_today = performance_data.get("posts_today", 0)
            if posts_today == 0:
                alerts.append("⚠️ No posts published today")
        
        return alerts
    
    def _generate_recommendations(
        self,
        metrics: List[PerformanceMetric],
        alerts: List[str],
        performance_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []
        
        # Metric-based recommendations
        retention_metric = next((m for m in metrics if "Retention" in m.metric_name), None)
        if retention_metric and retention_metric.trend == "down":
            recommendations.append("Revisar hooks de los primeros 3 segundos - retención bajando")
        
        views_metric = next((m for m in metrics if "Views" in m.metric_name), None)
        if views_metric and views_metric.trend == "down":
            recommendations.append("Aumentar frecuencia de posting - alcance disminuyendo")
        
        # Performance-based recommendations
        if performance_data:
            avg_retention = performance_data.get("avg_retention", 0)
            if avg_retention < 0.65:
                recommendations.append("Reducir duración de videos - retención por debajo de objetivo")
        
        # Alert-based recommendations
        if len(alerts) > 3:
            recommendations.append("Múltiples alertas - revisar estrategia general de contenido")
        
        return recommendations
    
    def _generate_tomorrow_focus(
        self,
        metrics: List[PerformanceMetric],
        alerts: List[str],
        recommendations: List[str]
    ) -> List[str]:
        """Generate tomorrow's focus areas."""
        focus = []
        
        # Address alerts
        if alerts:
            focus.append("Corregir métricas en decline")
        
        # Leverage successes
        up_metrics = [m for m in metrics if m.trend == "up"]
        if up_metrics:
            focus.append(f"Capitalizar momentum en {up_metrics[0].metric_name}")
        
        # Implement recommendations
        if recommendations:
            focus.append("Implementar recomendaciones estratégicas")
        
        # Default focuses
        if not focus:
            focus = [
                "Mantener consistencia de posting",
                "Monitorear engagement en tiempo real",
                "Preparar contenido para próxima semana"
            ]
        
        return focus
    
    def _generate_stub_report(self, user_id: str, date: datetime) -> DailyReport:
        """Generate stub report for testing."""
        return DailyReport(
            report_id=f"report_{user_id}_{date.strftime('%Y%m%d')}",
            date=date,
            user_id=user_id,
            posts_published=3,
            official_posts=2,
            satellite_posts=1,
            total_views=45000,
            total_engagement=3200,
            avg_retention=0.76,
            avg_ctr=0.082,
            metrics=[
                PerformanceMetric(
                    metric_name="Total Views",
                    value=45000.0,
                    change_percentage=12.5,
                    trend="up"
                ),
                PerformanceMetric(
                    metric_name="Avg Retention",
                    value=0.76,
                    change_percentage=3.2,
                    trend="up"
                ),
                PerformanceMetric(
                    metric_name="Avg CTR",
                    value=0.082,
                    change_percentage=-1.8,
                    trend="stable"
                )
            ],
            best_post_id="post_20241207_001",
            best_post_reason="78.5% retention - purple night aesthetic",
            worst_post_id="post_20241207_003",
            worst_post_reason="68.2% retention - daytime content",
            followers_change=150,
            audience_growth_rate=0.025,
            alerts=[],
            recommendations=[
                "Continuar con estética purple night - alta performance",
                "Reducir contenido diurno - menor engagement",
                "Aumentar frecuencia en horario 20:00-22:00"
            ],
            tomorrow_focus=[
                "Publicar contenido purple aesthetic",
                "Testear nuevo formato en satélite",
                "Monitorear comentarios para detectar hype"
            ],
            generated_at=datetime.utcnow()
        )
    
    def export_report_markdown(self, report: DailyReport) -> str:
        """
        Export report as markdown for Telegram Bot.
        
        Args:
            report: Daily report
        
        Returns:
            Markdown formatted report
        """
        md = f"""# 📊 Daily Report - {report.date.strftime('%Y-%m-%d')}

## 📝 Publications Summary
- **Posts Published**: {report.posts_published}
- **Official**: {report.official_posts}
- **Satellite**: {report.satellite_posts}

## 📈 Performance Metrics
- **Total Views**: {report.total_views:,}
- **Total Engagement**: {report.total_engagement:,}
- **Avg Retention**: {report.avg_retention*100:.1f}%
- **Avg CTR**: {report.avg_ctr*100:.2f}%

"""
        
        if report.metrics:
            md += "### Key Metrics Trends\n"
            for metric in report.metrics:
                emoji = "📈" if metric.trend == "up" else ("📉" if metric.trend == "down" else "➡️")
                md += f"- {emoji} **{metric.metric_name}**: {metric.value:.1f} ({metric.change_percentage:+.1f}%)\n"
            md += "\n"
        
        if report.best_post_id:
            md += f"### 🏆 Best Performer\n- **ID**: {report.best_post_id}\n- **Reason**: {report.best_post_reason}\n\n"
        
        if report.alerts:
            md += "### ⚠️ Alerts\n"
            for alert in report.alerts:
                md += f"- {alert}\n"
            md += "\n"
        
        if report.recommendations:
            md += "### 💡 Recommendations\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"
            md += "\n"
        
        if report.tomorrow_focus:
            md += "### 🎯 Tomorrow's Focus\n"
            for focus in report.tomorrow_focus:
                md += f"- {focus}\n"
        
        return md
