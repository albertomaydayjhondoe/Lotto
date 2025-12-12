"""
Model Metrics Store - Storage for performance metrics and learning data

Stores:
- Retention metrics per clip
- Engagement metrics
- Viewer behavior
- Engine performance
- Satellite performance
- Meta-learning scores
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from pathlib import Path
import logging
import json
import sqlite3
from collections import defaultdict

from .schemas_metrics import (
    MetricType,
    RetentionMetrics,
    EngagementMetrics,
    ViewerBehaviorMetrics,
    EnginePerformanceMetrics,
    SatellitePerformanceMetrics,
    MetaLearningScore,
    DailySnapshot,
    MetricsWriteRequest,
    MetricsReadRequest,
    Platform,
    ChannelType
)

logger = logging.getLogger(__name__)


class ModelMetricsStore:
    """
    Storage for ML model metrics and performance data.
    
    Uses SQLite for structured storage (can be replaced with PostgreSQL for production).
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        in_memory: bool = False
    ):
        """
        Initialize metrics store.
        
        Args:
            db_path: Path to SQLite database
            in_memory: Use in-memory database (for testing)
        """
        if in_memory:
            self.db_path = ":memory:"
        elif db_path:
            self.db_path = db_path
        else:
            storage_path = Path("/workspaces/stakazo/backend/storage/metrics")
            storage_path.mkdir(parents=True, exist_ok=True)
            self.db_path = str(storage_path / "metrics.db")
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self._init_tables()
        logger.info(f"ModelMetricsStore initialized: {self.db_path}")
    
    def _init_tables(self):
        """Initialize database tables."""
        cursor = self.conn.cursor()
        
        # Retention metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retention_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_type TEXT NOT NULL,
                avg_watch_time_sec REAL,
                avg_watch_percentage REAL,
                retention_curve TEXT,
                drop_off_points TEXT,
                peak_rewatch_time INTEGER,
                completion_rate REAL,
                rewatch_rate REAL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(content_id, platform, measured_at)
            )
        """)
        
        # Engagement metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_type TEXT NOT NULL,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                shares INTEGER,
                saves INTEGER,
                ctr REAL,
                engagement_rate REAL,
                save_rate REAL,
                views_velocity REAL,
                engagement_velocity REAL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(content_id, platform, measured_at)
            )
        """)
        
        # Viewer behavior
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viewer_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                avg_session_duration REAL,
                bounce_rate REAL,
                return_viewer_rate REAL,
                avg_time_to_first_interaction REAL,
                avg_time_to_like REAL,
                avg_time_to_comment REAL,
                mobile_vs_desktop TEXT,
                time_of_day_distribution TEXT,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(content_id, platform, measured_at)
            )
        """)
        
        # Engine performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engine_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine_name TEXT NOT NULL,
                predictions_made INTEGER,
                predictions_correct INTEGER,
                accuracy REAL,
                mae REAL,
                rmse REAL,
                best_predictions TEXT,
                worst_predictions TEXT,
                avg_inference_time_ms REAL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Satellite performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS satellite_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                satellite_account_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                followers_start INTEGER,
                followers_end INTEGER,
                followers_growth INTEGER,
                followers_growth_rate REAL,
                posts_count INTEGER,
                avg_views REAL,
                avg_engagement_rate REAL,
                avg_retention REAL,
                top_content_ids TEXT,
                cost_per_follower REAL,
                roi REAL,
                period_start DATE,
                period_end DATE,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(satellite_account_id, platform, period_start, period_end)
            )
        """)
        
        # Meta-learning scores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta_learning_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                overall_score REAL,
                retention_score REAL,
                engagement_score REAL,
                virality_score REAL,
                brand_alignment_score REAL,
                factors TEXT,
                strengths TEXT,
                weaknesses TEXT,
                improvement_suggestions TEXT,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(content_id, computed_at)
            )
        """)
        
        # Daily snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL UNIQUE,
                snapshot_id TEXT NOT NULL,
                total_content_analyzed INTEGER,
                total_views INTEGER,
                total_engagement INTEGER,
                avg_retention REAL,
                avg_engagement_rate REAL,
                avg_quality_score REAL,
                best_content_ids TEXT,
                best_patterns TEXT,
                satellite_metrics TEXT,
                engine_metrics TEXT,
                insights TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_retention_content ON retention_metrics(content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_content ON engagement_metrics(content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_learning_content ON meta_learning_scores(content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(snapshot_date)")
        
        self.conn.commit()
        logger.info("Database tables initialized")
    
    async def write_metrics(
        self,
        request: MetricsWriteRequest
    ) -> Dict[str, Any]:
        """
        Write metrics to storage.
        
        Args:
            request: Metrics write request
            
        Returns:
            Result dict
        """
        try:
            if request.metric_type == MetricType.RETENTION:
                return await self._write_retention_metrics(request)
            elif request.metric_type == MetricType.ENGAGEMENT:
                return await self._write_engagement_metrics(request)
            elif request.metric_type == MetricType.VIEWER_BEHAVIOR:
                return await self._write_viewer_behavior(request)
            elif request.metric_type == MetricType.ENGINE_PERFORMANCE:
                return await self._write_engine_performance(request)
            elif request.metric_type == MetricType.SATELLITE_PERFORMANCE:
                return await self._write_satellite_performance(request)
            elif request.metric_type == MetricType.LEARNING_SCORE:
                return await self._write_meta_learning_score(request)
            else:
                return {
                    "success": False,
                    "error": f"Unknown metric type: {request.metric_type}"
                }
        except Exception as e:
            logger.error(f"Failed to write metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _write_retention_metrics(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write retention metrics."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO retention_metrics (
                content_id, platform, channel_type,
                avg_watch_time_sec, avg_watch_percentage,
                retention_curve, drop_off_points,
                peak_rewatch_time, completion_rate, rewatch_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.content_id,
            request.platform.value if request.platform else data.get("platform"),
            request.channel_type.value if request.channel_type else data.get("channel_type"),
            data.get("avg_watch_time_sec"),
            data.get("avg_watch_percentage"),
            json.dumps(data.get("retention_curve", [])),
            json.dumps(data.get("drop_off_points", [])),
            data.get("peak_rewatch_time"),
            data.get("completion_rate"),
            data.get("rewatch_rate")
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "retention",
            "content_id": request.content_id
        }
    
    async def _write_engagement_metrics(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write engagement metrics."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO engagement_metrics (
                content_id, platform, channel_type,
                views, likes, comments, shares, saves,
                ctr, engagement_rate, save_rate,
                views_velocity, engagement_velocity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.content_id,
            request.platform.value if request.platform else data.get("platform"),
            request.channel_type.value if request.channel_type else data.get("channel_type"),
            data.get("views"),
            data.get("likes"),
            data.get("comments"),
            data.get("shares"),
            data.get("saves"),
            data.get("ctr"),
            data.get("engagement_rate"),
            data.get("save_rate"),
            data.get("views_velocity"),
            data.get("engagement_velocity")
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "engagement",
            "content_id": request.content_id
        }
    
    async def _write_viewer_behavior(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write viewer behavior metrics."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO viewer_behavior (
                content_id, platform,
                avg_session_duration, bounce_rate, return_viewer_rate,
                avg_time_to_first_interaction, avg_time_to_like, avg_time_to_comment,
                mobile_vs_desktop, time_of_day_distribution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.content_id,
            request.platform.value if request.platform else data.get("platform"),
            data.get("avg_session_duration"),
            data.get("bounce_rate"),
            data.get("return_viewer_rate"),
            data.get("avg_time_to_first_interaction"),
            data.get("avg_time_to_like"),
            data.get("avg_time_to_comment"),
            json.dumps(data.get("mobile_vs_desktop", {})),
            json.dumps(data.get("time_of_day_distribution", {}))
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "viewer_behavior",
            "content_id": request.content_id
        }
    
    async def _write_engine_performance(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write engine performance metrics."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO engine_performance (
                engine_name, predictions_made, predictions_correct,
                accuracy, mae, rmse,
                best_predictions, worst_predictions,
                avg_inference_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("engine_name"),
            data.get("predictions_made"),
            data.get("predictions_correct"),
            data.get("accuracy"),
            data.get("mae"),
            data.get("rmse"),
            json.dumps(data.get("best_predictions", [])),
            json.dumps(data.get("worst_predictions", [])),
            data.get("avg_inference_time_ms")
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "engine_performance",
            "engine_name": data.get("engine_name")
        }
    
    async def _write_satellite_performance(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write satellite performance metrics."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO satellite_performance (
                satellite_account_id, platform,
                followers_start, followers_end, followers_growth, followers_growth_rate,
                posts_count, avg_views, avg_engagement_rate, avg_retention,
                top_content_ids, cost_per_follower, roi,
                period_start, period_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("satellite_account_id"),
            request.platform.value if request.platform else data.get("platform"),
            data.get("followers_start"),
            data.get("followers_end"),
            data.get("followers_growth"),
            data.get("followers_growth_rate"),
            data.get("posts_count"),
            data.get("avg_views"),
            data.get("avg_engagement_rate"),
            data.get("avg_retention"),
            json.dumps(data.get("top_content_ids", [])),
            data.get("cost_per_follower"),
            data.get("roi"),
            data.get("period_start"),
            data.get("period_end")
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "satellite_performance",
            "satellite_account_id": data.get("satellite_account_id")
        }
    
    async def _write_meta_learning_score(self, request: MetricsWriteRequest) -> Dict[str, Any]:
        """Write meta-learning score."""
        data = request.data
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO meta_learning_scores (
                content_id, overall_score,
                retention_score, engagement_score, virality_score, brand_alignment_score,
                factors, strengths, weaknesses, improvement_suggestions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.content_id,
            data.get("overall_score"),
            data.get("retention_score"),
            data.get("engagement_score"),
            data.get("virality_score"),
            data.get("brand_alignment_score"),
            json.dumps(data.get("factors", {})),
            json.dumps(data.get("strengths", [])),
            json.dumps(data.get("weaknesses", [])),
            json.dumps(data.get("improvement_suggestions", []))
        ))
        
        self.conn.commit()
        
        return {
            "success": True,
            "metric_type": "meta_learning_score",
            "content_id": request.content_id
        }
    
    async def read_metrics(
        self,
        request: MetricsReadRequest
    ) -> Dict[str, Any]:
        """
        Read metrics from storage.
        
        Args:
            request: Metrics read request
            
        Returns:
            Metrics data
        """
        try:
            results = {}
            
            if not request.metric_types or MetricType.RETENTION in request.metric_types:
                results["retention"] = await self._read_retention_metrics(request)
            
            if not request.metric_types or MetricType.ENGAGEMENT in request.metric_types:
                results["engagement"] = await self._read_engagement_metrics(request)
            
            if not request.metric_types or MetricType.LEARNING_SCORE in request.metric_types:
                results["learning_scores"] = await self._read_meta_learning_scores(request)
            
            return {
                "success": True,
                "metrics": results,
                "count": sum(len(v) for v in results.values() if isinstance(v, list))
            }
            
        except Exception as e:
            logger.error(f"Failed to read metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _read_retention_metrics(self, request: MetricsReadRequest) -> List[Dict[str, Any]]:
        """Read retention metrics."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM retention_metrics WHERE 1=1"
        params = []
        
        if request.content_ids:
            placeholders = ",".join("?" * len(request.content_ids))
            query += f" AND content_id IN ({placeholders})"
            params.extend(request.content_ids)
        
        if request.platform:
            query += " AND platform = ?"
            params.append(request.platform.value)
        
        query += f" LIMIT {request.limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def _read_engagement_metrics(self, request: MetricsReadRequest) -> List[Dict[str, Any]]:
        """Read engagement metrics."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM engagement_metrics WHERE 1=1"
        params = []
        
        if request.content_ids:
            placeholders = ",".join("?" * len(request.content_ids))
            query += f" AND content_id IN ({placeholders})"
            params.extend(request.content_ids)
        
        if request.platform:
            query += " AND platform = ?"
            params.append(request.platform.value)
        
        query += f" LIMIT {request.limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def _read_meta_learning_scores(self, request: MetricsReadRequest) -> List[Dict[str, Any]]:
        """Read meta-learning scores."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM meta_learning_scores WHERE 1=1"
        params = []
        
        if request.content_ids:
            placeholders = ",".join("?" * len(request.content_ids))
            query += f" AND content_id IN ({placeholders})"
            params.extend(request.content_ids)
        
        query += f" ORDER BY computed_at DESC LIMIT {request.limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def write_daily_snapshot(
        self,
        snapshot: DailySnapshot
    ) -> Dict[str, Any]:
        """Write daily snapshot."""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_snapshots (
                    snapshot_date, snapshot_id,
                    total_content_analyzed, total_views, total_engagement,
                    avg_retention, avg_engagement_rate, avg_quality_score,
                    best_content_ids, best_patterns,
                    satellite_metrics, engine_metrics,
                    insights, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_date.isoformat(),
                snapshot.snapshot_id,
                snapshot.total_content_analyzed,
                snapshot.total_views,
                snapshot.total_engagement,
                snapshot.avg_retention,
                snapshot.avg_engagement_rate,
                snapshot.avg_quality_score,
                json.dumps(snapshot.best_content_ids),
                json.dumps(snapshot.best_patterns),
                json.dumps(snapshot.satellite_metrics),
                json.dumps(snapshot.engine_metrics),
                json.dumps(snapshot.insights),
                json.dumps(snapshot.recommendations)
            ))
            
            self.conn.commit()
            
            return {
                "success": True,
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_date": snapshot.snapshot_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to write daily snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_daily_snapshots(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> List[DailySnapshot]:
        """Read daily snapshots."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM daily_snapshots WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND snapshot_date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND snapshot_date <= ?"
            params.append(end_date.isoformat())
        
        query += f" ORDER BY snapshot_date DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        snapshots = []
        for row in rows:
            row_dict = dict(row)
            # Parse JSON fields
            row_dict["best_content_ids"] = json.loads(row_dict["best_content_ids"])
            row_dict["best_patterns"] = json.loads(row_dict["best_patterns"])
            row_dict["satellite_metrics"] = json.loads(row_dict["satellite_metrics"])
            row_dict["engine_metrics"] = json.loads(row_dict["engine_metrics"])
            row_dict["insights"] = json.loads(row_dict["insights"])
            row_dict["recommendations"] = json.loads(row_dict["recommendations"])
            
            snapshots.append(DailySnapshot(**row_dict))
        
        return snapshots
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
