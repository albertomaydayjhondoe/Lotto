"""
Winner Engine - Publication Winner Selection

Selecciona el creative ganador para publicación basado en performance real:
ROAS, CTR, CVR, ViewDepth.

Integrado con:
- ROAS Engine (10.5)
- A/B Testing (10.4)
- Targeting Optimizer (10.12)
"""
import logging
import random
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.meta_creative_intelligence.schemas import (
    PerformanceMetrics,
    WinnerSelectionRequest,
    WinnerSelectionResponse,
)

logger = logging.getLogger(__name__)


class WinnerEngine:
    """
    Selecciona el creative ganador basado en métricas reales.
    
    STUB Mode: Simula métricas y selección
    LIVE Mode: Integra con ROAS Engine, Meta Insights, A/B Testing
    """
    
    def __init__(self, mode: str = "stub"):
        """
        Args:
            mode: "stub" o "live"
        """
        self.mode = mode
        logger.info(f"WinnerEngine initialized in {mode} mode")
    
    async def select_winner(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        candidate_asset_ids: list[UUID],
        criteria_weights: dict[str, float],
        min_impressions: int = 1000,
    ) -> WinnerSelectionResponse:
        """
        Selecciona el creative ganador.
        
        Args:
            db: Database session
            campaign_id: ID de la campaña
            candidate_asset_ids: IDs de los assets candidatos
            criteria_weights: Pesos de criterios {"roas": 0.4, "ctr": 0.25, ...}
            min_impressions: Mínimo de impresiones para considerar
            
        Returns:
            WinnerSelectionResponse con el ganador seleccionado
        """
        logger.info(f"Selecting winner for campaign {campaign_id} from {len(candidate_asset_ids)} candidates")
        
        # 1. Obtener métricas de performance para cada candidato
        candidate_metrics = {}
        for asset_id in candidate_asset_ids:
            metrics = await self._get_performance_metrics(db, campaign_id, asset_id)
            
            # Filtrar por mínimo de impresiones
            if metrics.impressions >= min_impressions:
                candidate_metrics[asset_id] = metrics
            else:
                logger.info(f"Asset {asset_id} excluded: only {metrics.impressions} impressions (min: {min_impressions})")
        
        if not candidate_metrics:
            raise ValueError(f"No candidates meet minimum impressions threshold ({min_impressions})")
        
        # 2. Calcular scores weighted para cada candidato
        all_scores = {}
        for asset_id, metrics in candidate_metrics.items():
            score = await self._calculate_weighted_score(metrics, criteria_weights)
            all_scores[str(asset_id)] = score
        
        # 3. Seleccionar ganador y runner-up
        sorted_candidates = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        winner_asset_id = UUID(sorted_candidates[0][0])
        winner_score = sorted_candidates[0][1]
        
        runner_up_asset_id = None
        runner_up_score = None
        if len(sorted_candidates) > 1:
            runner_up_asset_id = UUID(sorted_candidates[1][0])
            runner_up_score = sorted_candidates[1][1]
        
        # 4. Generar reasoning
        winner_metrics = candidate_metrics[winner_asset_id]
        reasoning = await self._generate_reasoning(winner_metrics, criteria_weights, winner_score)
        
        # 5. Performance summary
        performance_summary = {
            "total_candidates": len(candidate_asset_ids),
            "qualified_candidates": len(candidate_metrics),
            "winner_roas": winner_metrics.roas,
            "winner_ctr": winner_metrics.ctr,
            "winner_cvr": winner_metrics.cvr,
            "winner_view_depth": winner_metrics.view_depth,
            "winner_impressions": winner_metrics.impressions,
            "winner_spend": winner_metrics.spend,
            "score_margin": winner_score - runner_up_score if runner_up_score else 0.0,
        }
        
        return WinnerSelectionResponse(
            selection_id=uuid4(),
            campaign_id=campaign_id,
            winner_asset_id=winner_asset_id,
            winner_score=winner_score,
            runner_up_asset_id=runner_up_asset_id,
            runner_up_score=runner_up_score,
            all_scores=all_scores,
            reasoning=reasoning,
            performance_summary=performance_summary,
            created_at=datetime.utcnow(),
        )
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    async def _get_performance_metrics(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        asset_id: UUID,
    ) -> PerformanceMetrics:
        """
        Obtiene métricas de performance del asset.
        
        STUB: Genera métricas sintéticas
        LIVE TODO: Integrar con:
        - MetaROASEngine (10.5)
        - MetaInsightsCollector (10.7)
        - MetaABTestingModel (10.4)
        
        from app.meta_ads_orchestrator.roas_engine import ROASEngine
        from app.meta_insights_collector.collector import MetaInsightsCollector
        
        roas_engine = ROASEngine(db)
        roas_data = await roas_engine.get_roas_for_asset(asset_id)
        
        insights_collector = MetaInsightsCollector(mode="live")
        insights = await insights_collector.get_insights_for_asset(asset_id)
        """
        if self.mode == "stub":
            return await self._get_performance_metrics_stub(asset_id)
        else:
            return await self._get_performance_metrics_live(db, campaign_id, asset_id)
    
    async def _get_performance_metrics_stub(self, asset_id: UUID) -> PerformanceMetrics:
        """STUB: Genera métricas sintéticas realistas"""
        # Generar métricas correlacionadas
        base_quality = random.uniform(0.5, 1.0)
        
        # ROAS: 0.5 - 5.0 (típico rango)
        roas = 0.5 + (base_quality * 4.5) + random.uniform(-0.3, 0.3)
        
        # CTR: 0.5% - 5% (Meta Ads típico)
        ctr = 0.005 + (base_quality * 0.045) + random.uniform(-0.005, 0.005)
        ctr = max(0.001, ctr)  # Mínimo 0.1%
        
        # CVR: 0.5% - 8% (típico e-commerce)
        cvr = 0.005 + (base_quality * 0.075) + random.uniform(-0.005, 0.005)
        cvr = max(0.001, cvr)
        
        # View Depth: 20% - 85% (% de video visto)
        view_depth = 0.20 + (base_quality * 0.65) + random.uniform(-0.1, 0.1)
        view_depth = max(0.1, min(1.0, view_depth))
        
        # Engagement rate: correlacionado
        engagement_rate = 0.02 + (base_quality * 0.08) + random.uniform(-0.01, 0.01)
        engagement_rate = max(0.01, engagement_rate)
        
        # Volume metrics
        impressions = random.randint(1000, 50000)
        clicks = int(impressions * ctr)
        conversions = int(clicks * cvr)
        spend = impressions * 0.01  # $0.01 CPM simplificado
        
        return PerformanceMetrics(
            roas=round(roas, 2),
            ctr=round(ctr, 4),
            cvr=round(cvr, 4),
            view_depth=round(view_depth, 2),
            engagement_rate=round(engagement_rate, 4),
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            spend=round(spend, 2),
        )
    
    async def _get_performance_metrics_live(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        asset_id: UUID,
    ) -> PerformanceMetrics:
        """
        TODO LIVE: Integrar con servicios reales
        """
        raise NotImplementedError("LIVE performance metrics not implemented yet")
    
    # ========================================================================
    # SCORING
    # ========================================================================
    
    async def _calculate_weighted_score(
        self,
        metrics: PerformanceMetrics,
        criteria_weights: dict[str, float],
    ) -> float:
        """
        Calcula score ponderado.
        
        Normalización:
        - ROAS: 0-5 → 0-100 (linear)
        - CTR: 0-5% → 0-100 (linear)
        - CVR: 0-8% → 0-100 (linear)
        - View Depth: 0-100% → 0-100 (direct)
        """
        # Normalizar métricas a escala 0-100
        roas_normalized = min((metrics.roas or 0) / 5.0 * 100, 100)
        ctr_normalized = min((metrics.ctr or 0) / 0.05 * 100, 100)
        cvr_normalized = min((metrics.cvr or 0) / 0.08 * 100, 100)
        view_depth_normalized = (metrics.view_depth or 0) * 100
        
        # Score ponderado
        score = (
            roas_normalized * criteria_weights.get("roas", 0.4) +
            ctr_normalized * criteria_weights.get("ctr", 0.25) +
            cvr_normalized * criteria_weights.get("cvr", 0.20) +
            view_depth_normalized * criteria_weights.get("view_depth", 0.15)
        )
        
        return round(score, 2)
    
    # ========================================================================
    # REASONING
    # ========================================================================
    
    async def _generate_reasoning(
        self,
        metrics: PerformanceMetrics,
        criteria_weights: dict[str, float],
        final_score: float,
    ) -> str:
        """Genera explicación de la selección"""
        reasons = []
        
        # Identificar puntos fuertes
        if metrics.roas and metrics.roas >= 3.0:
            reasons.append(f"Excellent ROAS of {metrics.roas:.2f} (weight: {criteria_weights.get('roas', 0.4):.0%})")
        
        if metrics.ctr and metrics.ctr >= 0.03:
            reasons.append(f"Strong CTR of {metrics.ctr*100:.2f}% (weight: {criteria_weights.get('ctr', 0.25):.0%})")
        
        if metrics.cvr and metrics.cvr >= 0.04:
            reasons.append(f"High CVR of {metrics.cvr*100:.2f}% (weight: {criteria_weights.get('cvr', 0.20):.0%})")
        
        if metrics.view_depth and metrics.view_depth >= 0.60:
            reasons.append(f"Good view depth of {metrics.view_depth*100:.0f}% (weight: {criteria_weights.get('view_depth', 0.15):.0%})")
        
        # Volume
        reasons.append(f"Based on {metrics.impressions:,} impressions, {metrics.clicks:,} clicks, {metrics.conversions} conversions")
        
        # Final summary
        summary = (
            f"Selected as winner with weighted score of {final_score:.2f}/100. "
            f"Key strengths: {'; '.join(reasons)}."
        )
        
        return summary
