"""
Metrics Collector
Recolección de métricas de engagement desde plataformas satélite.

Sprint 2 - Satellite Engine
Author: AI Architect
Date: 2025-12-07
"""

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.satellites.models import (
    PlatformMetrics,
    MetricsSnapshot,
    SatelliteAccount,
    PlatformType
)
from app.satellites.config import SatelliteConfig
from app.satellites.platforms import (
    TikTokClient,
    InstagramClient,
    YouTubeClient
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collector para métricas de engagement multi-plataforma.
    
    Features:
    - Polling periódico de métricas
    - Aggregation por plataforma
    - Historical snapshots
    - ML signals preparation (TODO Sprint 3)
    """
    
    def __init__(self, config: SatelliteConfig):
        """
        Inicializar metrics collector.
        
        Args:
            config: Configuración del Satellite Engine
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform clients
        self.clients = {
            "tiktok": TikTokClient(config),
            "instagram": InstagramClient(config),
            "youtube": YouTubeClient(config),
        }
        
        # Metrics storage
        self.metrics_buffer: List[PlatformMetrics] = []
        self.snapshots: List[MetricsSnapshot] = []
        
        # Tracking
        self.tracked_posts: Dict[str, Dict[str, any]] = {}  # post_id -> {platform, account, last_collected}
    
    def track_post(
        self,
        post_id: str,
        platform: PlatformType,
        account: SatelliteAccount
    ) -> None:
        """
        Agregar post para tracking de métricas.
        
        Args:
            post_id: ID del post en la plataforma
            platform: Plataforma del post
            account: Cuenta asociada
        """
        self.tracked_posts[post_id] = {
            "platform": platform,
            "account": account,
            "last_collected": None,
            "added_at": datetime.utcnow()
        }
        
        self.logger.info(f"Now tracking post {post_id} on {platform}")
    
    def stop_tracking(
        self,
        post_id: str
    ) -> bool:
        """
        Dejar de trackear un post.
        
        Args:
            post_id: ID del post
            
        Returns:
            True si se removió
        """
        if post_id in self.tracked_posts:
            del self.tracked_posts[post_id]
            self.logger.info(f"Stopped tracking post {post_id}")
            return True
        return False
    
    async def collect_metrics(self) -> List[PlatformMetrics]:
        """
        Recolectar métricas de todos los posts trackeados.
        
        Returns:
            Lista de PlatformMetrics recolectadas
        """
        if not self.config.enable_metrics_collection:
            self.logger.debug("Metrics collection disabled")
            return []
        
        collected = []
        
        for post_id, info in self.tracked_posts.items():
            try:
                platform = info["platform"]
                account = info["account"]
                client = self.clients.get(platform)
                
                if not client:
                    self.logger.error(f"No client for platform: {platform}")
                    continue
                
                # Collect metrics
                metrics = await client.get_metrics(post_id, account)
                
                # Store in buffer
                self.metrics_buffer.append(metrics)
                collected.append(metrics)
                
                # Update tracking info
                self.tracked_posts[post_id]["last_collected"] = datetime.utcnow()
                
                self.logger.debug(
                    f"Collected metrics for {post_id}: "
                    f"{metrics.views} views, {metrics.engagement_rate:.2%} engagement"
                )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to collect metrics for {post_id}: {e}",
                    exc_info=True
                )
        
        return collected
    
    async def collect_metrics_loop(self) -> None:
        """
        Loop de recolección periódica (ejecutar en background).
        
        Esta función debe ejecutarse continuamente en un background task.
        """
        self.logger.info("Starting metrics collection loop")
        
        while True:
            try:
                if self.tracked_posts:
                    self.logger.info(
                        f"Collecting metrics for {len(self.tracked_posts)} posts"
                    )
                    await self.collect_metrics()
                
                # Create snapshot
                await self._create_snapshots()
                
                # Sleep until next collection
                await asyncio.sleep(self.config.metrics_collection_interval_sec)
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    def get_metrics_for_post(
        self,
        post_id: str
    ) -> List[PlatformMetrics]:
        """
        Obtener todas las métricas históricas de un post.
        
        Args:
            post_id: ID del post
            
        Returns:
            Lista de métricas ordenadas por timestamp
        """
        metrics = [m for m in self.metrics_buffer if m.post_id == post_id]
        return sorted(metrics, key=lambda m: m.collected_at)
    
    def get_metrics_for_platform(
        self,
        platform: PlatformType
    ) -> List[PlatformMetrics]:
        """
        Obtener métricas de una plataforma.
        
        Args:
            platform: Plataforma a consultar
            
        Returns:
            Lista de métricas
        """
        return [m for m in self.metrics_buffer if m.platform == platform]
    
    async def _create_snapshots(self) -> None:
        """Crear snapshots agregados por plataforma."""
        now = datetime.utcnow()
        
        for platform in ["tiktok", "instagram", "youtube"]:
            # Get recent metrics (last 24h)
            cutoff = now - timedelta(days=1)
            recent_metrics = [
                m for m in self.metrics_buffer
                if m.platform == platform and m.collected_at >= cutoff
            ]
            
            if not recent_metrics:
                continue
            
            # Calculate aggregates
            total_views = sum(m.views for m in recent_metrics)
            total_engagement = sum(
                m.likes + m.comments + m.shares + m.saves
                for m in recent_metrics
            )
            
            avg_engagement_rate = (
                sum(m.engagement_rate for m in recent_metrics) / len(recent_metrics)
                if recent_metrics else 0.0
            )
            
            avg_completion_rate = (
                sum(m.completion_rate for m in recent_metrics) / len(recent_metrics)
                if recent_metrics else 0.0
            )
            
            # Create snapshot
            snapshot = MetricsSnapshot(
                snapshot_id=f"{platform}_{now.timestamp()}",
                platform=platform,
                total_posts=len(recent_metrics),
                total_views=total_views,
                total_engagement=total_engagement,
                avg_engagement_rate=avg_engagement_rate,
                avg_completion_rate=avg_completion_rate,
                from_date=cutoff,
                to_date=now
            )
            
            self.snapshots.append(snapshot)
            
            # Keep only last 100 snapshots per platform
            platform_snapshots = [s for s in self.snapshots if s.platform == platform]
            if len(platform_snapshots) > 100:
                # Remove oldest
                oldest = sorted(platform_snapshots, key=lambda s: s.collected_at)[:len(platform_snapshots)-100]
                for old_snapshot in oldest:
                    self.snapshots.remove(old_snapshot)
    
    def get_snapshots(
        self,
        platform: Optional[PlatformType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[MetricsSnapshot]:
        """
        Obtener snapshots con filtros opcionales.
        
        Args:
            platform: Filtrar por plataforma
            from_date: Fecha inicio
            to_date: Fecha fin
            
        Returns:
            Lista de MetricsSnapshot
        """
        snapshots = self.snapshots
        
        if platform:
            snapshots = [s for s in snapshots if s.platform == platform]
        
        if from_date:
            snapshots = [s for s in snapshots if s.collected_at >= from_date]
        
        if to_date:
            snapshots = [s for s in snapshots if s.collected_at <= to_date]
        
        return sorted(snapshots, key=lambda s: s.collected_at, reverse=True)
    
    def get_summary(self) -> Dict:
        """
        Obtener resumen de métricas globales.
        
        Returns:
            Dict con resumen
        """
        return {
            "tracked_posts": len(self.tracked_posts),
            "total_metrics_collected": len(self.metrics_buffer),
            "snapshots_created": len(self.snapshots),
            "platforms": {
                platform: len([m for m in self.metrics_buffer if m.platform == platform])
                for platform in ["tiktok", "instagram", "youtube"]
            }
        }
    
    def clear_old_metrics(
        self,
        days: int = 30
    ) -> int:
        """
        Limpiar métricas antiguas del buffer.
        
        Args:
            days: Días a mantener
            
        Returns:
            Número de métricas eliminadas
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        before_count = len(self.metrics_buffer)
        self.metrics_buffer = [
            m for m in self.metrics_buffer
            if m.collected_at >= cutoff
        ]
        after_count = len(self.metrics_buffer)
        
        removed = before_count - after_count
        
        if removed > 0:
            self.logger.info(f"Cleared {removed} old metrics (older than {days} days)")
        
        return removed
