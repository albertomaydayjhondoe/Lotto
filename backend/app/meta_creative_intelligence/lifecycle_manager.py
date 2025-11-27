"""
Lifecycle Manager - Creative Fatigue Detection & Renewal

Detecta fatiga de creatividades y gestiona renovación automática.
"""
import logging
import random
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.meta_creative_intelligence.schemas import (
    FatigueDetectionResult,
    RenewalRequest,
    RenewalResponse,
)

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Gestiona el ciclo de vida de creatividades.
    
    Detecta:
    - Creative fatigue (CTR/CVR declining)
    - Frequency saturation
    - Engagement drop
    
    Acciones:
    - Generate variant
    - Replace entirely
    - Refresh targeting
    """
    
    def __init__(self, mode: str = "stub"):
        """
        Args:
            mode: "stub" o "live"
        """
        self.mode = mode
        logger.info(f"LifecycleManager initialized in {mode} mode")
    
    # ========================================================================
    # FATIGUE DETECTION
    # ========================================================================
    
    async def detect_fatigue(
        self,
        db: AsyncSession,
        creative_id: UUID,
    ) -> FatigueDetectionResult:
        """
        Detecta fatiga de un creative.
        
        Criterios:
        - CTR drop ≥30% vs. baseline
        - CVR drop ≥25% vs. baseline
        - Frequency ≥5 impressions per user
        - Days active >14
        
        Args:
            db: Database session
            creative_id: ID del creative
            
        Returns:
            FatigueDetectionResult
        """
        logger.info(f"Detecting fatigue for creative {creative_id}")
        
        # Obtener métricas históricas
        metrics_trend = await self._get_metrics_trend(db, creative_id)
        
        # Calcular fatigue score
        fatigue_score = await self._calculate_fatigue_score(metrics_trend)
        
        # Determinar si está fatigado
        is_fatigued = fatigue_score >= 70.0
        
        # Generar recomendación
        recommendation = await self._generate_fatigue_recommendation(fatigue_score, metrics_trend)
        
        return FatigueDetectionResult(
            creative_id=creative_id,
            is_fatigued=is_fatigued,
            fatigue_score=fatigue_score,
            metrics_trend=metrics_trend,
            recommendation=recommendation,
            days_active=metrics_trend.get("days_active", 0),
            impressions_total=metrics_trend.get("impressions_total", 0),
        )
    
    async def _get_metrics_trend(
        self,
        db: AsyncSession,
        creative_id: UUID,
    ) -> dict:
        """
        Obtiene tendencias de métricas.
        
        STUB: Genera datos sintéticos
        LIVE TODO: Consultar MetaInsightsCollector con ventana temporal
        
        from app.meta_insights_collector.collector import MetaInsightsCollector
        collector = MetaInsightsCollector(mode="live")
        
        # Últimos 7 días
        recent = await collector.get_insights(creative_id, days=7)
        # Baseline (días 8-14)
        baseline = await collector.get_insights(creative_id, days_start=8, days_end=14)
        
        ctr_drop = (baseline.ctr - recent.ctr) / baseline.ctr
        cvr_drop = (baseline.cvr - recent.cvr) / baseline.cvr
        """
        if self.mode == "stub":
            return await self._get_metrics_trend_stub(creative_id)
        else:
            return await self._get_metrics_trend_live(db, creative_id)
    
    async def _get_metrics_trend_stub(self, creative_id: UUID) -> dict:
        """STUB: Genera tendencia sintética"""
        days_active = random.randint(7, 60)
        impressions_total = random.randint(5000, 500000)
        
        # Simular degradación
        degradation_factor = min(days_active / 30.0, 1.0)  # Más días = más degradación
        
        # Baseline (primeros 7 días)
        baseline_ctr = random.uniform(0.02, 0.05)
        baseline_cvr = random.uniform(0.015, 0.04)
        baseline_engagement = random.uniform(0.03, 0.08)
        
        # Recent (últimos 7 días) - con degradación
        recent_ctr = baseline_ctr * (1 - degradation_factor * random.uniform(0.2, 0.5))
        recent_cvr = baseline_cvr * (1 - degradation_factor * random.uniform(0.15, 0.4))
        recent_engagement = baseline_engagement * (1 - degradation_factor * random.uniform(0.1, 0.3))
        
        # Drops
        ctr_drop = (baseline_ctr - recent_ctr) / baseline_ctr if baseline_ctr > 0 else 0
        cvr_drop = (baseline_cvr - recent_cvr) / baseline_cvr if baseline_cvr > 0 else 0
        engagement_drop = (baseline_engagement - recent_engagement) / baseline_engagement if baseline_engagement > 0 else 0
        
        # Frequency
        avg_frequency = impressions_total / max(days_active * 100, 1)  # Impressions per day per 100 users
        
        return {
            "days_active": days_active,
            "impressions_total": impressions_total,
            "baseline_ctr": round(baseline_ctr, 4),
            "recent_ctr": round(recent_ctr, 4),
            "ctr_drop_pct": round(ctr_drop * 100, 1),
            "baseline_cvr": round(baseline_cvr, 4),
            "recent_cvr": round(recent_cvr, 4),
            "cvr_drop_pct": round(cvr_drop * 100, 1),
            "baseline_engagement": round(baseline_engagement, 4),
            "recent_engagement": round(recent_engagement, 4),
            "engagement_drop_pct": round(engagement_drop * 100, 1),
            "avg_frequency": round(avg_frequency, 2),
        }
    
    async def _get_metrics_trend_live(self, db: AsyncSession, creative_id: UUID) -> dict:
        """TODO LIVE: Integrar con insights collector"""
        raise NotImplementedError("LIVE metrics trend not implemented yet")
    
    async def _calculate_fatigue_score(self, metrics_trend: dict) -> float:
        """
        Calcula score de fatiga (0-100).
        
        Factores:
        - CTR drop (40%)
        - CVR drop (30%)
        - Engagement drop (20%)
        - Frequency saturation (10%)
        """
        score = 0.0
        
        # CTR drop score (0-40)
        ctr_drop = metrics_trend.get("ctr_drop_pct", 0) / 100.0
        score += min(ctr_drop * 100 * 0.40, 40)
        
        # CVR drop score (0-30)
        cvr_drop = metrics_trend.get("cvr_drop_pct", 0) / 100.0
        score += min(cvr_drop * 100 * 0.30, 30)
        
        # Engagement drop score (0-20)
        engagement_drop = metrics_trend.get("engagement_drop_pct", 0) / 100.0
        score += min(engagement_drop * 100 * 0.20, 20)
        
        # Frequency saturation score (0-10)
        avg_frequency = metrics_trend.get("avg_frequency", 0)
        if avg_frequency >= 5.0:
            score += 10
        elif avg_frequency >= 3.0:
            score += 5
        
        return round(score, 2)
    
    async def _generate_fatigue_recommendation(
        self,
        fatigue_score: float,
        metrics_trend: dict,
    ) -> str:
        """Genera recomendación basada en fatigue score"""
        if fatigue_score >= 80:
            return (
                "CRITICAL FATIGUE - Immediate action required. "
                f"CTR dropped {metrics_trend.get('ctr_drop_pct', 0):.1f}%, "
                f"CVR dropped {metrics_trend.get('cvr_drop_pct', 0):.1f}%. "
                "Recommendation: Replace creative entirely or pause campaign."
            )
        elif fatigue_score >= 70:
            return (
                "HIGH FATIGUE - Generate new variant or refresh targeting. "
                f"Performance declining significantly after {metrics_trend.get('days_active', 0)} days."
            )
        elif fatigue_score >= 50:
            return (
                "MODERATE FATIGUE - Consider generating variant or adjusting frequency caps. "
                "Performance still acceptable but showing decline."
            )
        else:
            return (
                "LOW FATIGUE - Creative is performing well. "
                "Continue monitoring but no action needed yet."
            )
    
    # ========================================================================
    # RENEWAL
    # ========================================================================
    
    async def renew_creative(
        self,
        db: AsyncSession,
        creative_id: UUID,
        strategy: str = "generate_variant",
        auto_apply: bool = False,
    ) -> RenewalResponse:
        """
        Renueva un creative fatigado.
        
        Estrategias:
        - generate_variant: Crear variante del mismo base
        - replace_entirely: Reemplazar con nuevo creative
        - refresh_targeting: Cambiar targeting sin tocar creative
        
        Args:
            db: Database session
            creative_id: ID del creative
            strategy: Estrategia de renovación
            auto_apply: Aplicar automáticamente o solo simular
            
        Returns:
            RenewalResponse
        """
        logger.info(f"Renewing creative {creative_id} with strategy '{strategy}'")
        
        actions_taken = []
        new_creative_id = None
        success = True
        message = ""
        
        try:
            if strategy == "generate_variant":
                # Generar variante del mismo video base
                actions_taken.append("Generated new variant from same base video")
                new_creative_id = uuid4()
                message = f"New variant created: {new_creative_id}"
                
                if auto_apply:
                    actions_taken.append("Paused fatigued creative")
                    actions_taken.append("Activated new variant")
                    message += " and automatically applied"
            
            elif strategy == "replace_entirely":
                # Reemplazar con creative completamente nuevo
                actions_taken.append("Selected new base video")
                new_creative_id = uuid4()
                message = f"New creative created: {new_creative_id}"
                
                if auto_apply:
                    actions_taken.append("Paused old creative")
                    actions_taken.append("Activated new creative")
                    message += " and automatically applied"
            
            elif strategy == "refresh_targeting":
                # Cambiar targeting sin tocar creative
                actions_taken.append("Refreshed targeting parameters")
                actions_taken.append("Expanded to new geographies")
                actions_taken.append("Updated interest targeting")
                message = "Targeting refreshed successfully"
                
                if auto_apply:
                    actions_taken.append("Applied new targeting to adsets")
                    message += " and automatically applied"
            
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        except Exception as e:
            success = False
            message = f"Renewal failed: {str(e)}"
            logger.error(message)
        
        return RenewalResponse(
            renewal_id=uuid4(),
            creative_id=creative_id,
            strategy=strategy,
            new_creative_id=new_creative_id,
            actions_taken=actions_taken,
            success=success,
            message=message,
            created_at=datetime.utcnow(),
        )
