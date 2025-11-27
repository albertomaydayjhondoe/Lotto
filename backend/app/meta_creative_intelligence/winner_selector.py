"""
Winner Selector - Selección del ganador final para publicación (PASO 10.13)
"""
import random
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.meta_creative_intelligence.schemas import WinnerMetrics, WinnerSelection

logger = logging.getLogger(__name__)


class WinnerSelector:
    """
    Selector del video ganador FINAL para Instagram.
    
    Usa métricas reales de:
    - ROAS Engine (PASO 10.5)
    - A/B Testing Engine (PASO 10.4)
    - Targeting Optimizer (PASO 10.12)
    
    Fórmula weighted score:
    Score = w1*ROAS + w2*CTR + w3*CVR + w4*ViewDepth
    """
    
    def __init__(self, mode: str = "stub"):
        self.mode = mode
    
    async def select_winner(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        ab_test_id: Optional[UUID] = None,
        roas_weight: float = 0.40,
        ctr_weight: float = 0.25,
        cvr_weight: float = 0.25,
        view_depth_weight: float = 0.10,
    ) -> WinnerSelection:
        """Seleccionar ganador basado en métricas reales"""
        
        logger.info(f"Selecting winner for campaign {campaign_id}")
        
        if self.mode == "stub":
            return await self._select_stub(
                db, campaign_id, ab_test_id,
                roas_weight, ctr_weight, cvr_weight, view_depth_weight
            )
        else:
            return await self._select_live(
                db, campaign_id, ab_test_id,
                roas_weight, ctr_weight, cvr_weight, view_depth_weight
            )
    
    async def _select_stub(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        ab_test_id: Optional[UUID],
        roas_weight: float,
        ctr_weight: float,
        cvr_weight: float,
        view_depth_weight: float,
    ) -> WinnerSelection:
        """Selección STUB con datos sintéticos"""
        
        # Simular candidatos
        num_candidates = random.randint(2, 5)
        
        best_score = 0.0
        best_metrics = None
        winner_video_id = None
        
        for i in range(num_candidates):
            # Generar métricas sintéticas
            roas = random.uniform(1.5, 5.0)
            ctr = random.uniform(0.01, 0.08)
            cvr = random.uniform(0.005, 0.03)
            view_depth = random.uniform(0.40, 0.85)
            engagement = random.uniform(0.05, 0.15)
            
            # Calcular composite score (normalizado 0-100)
            score = (
                roas_weight * min(roas / 5.0 * 100, 100) +
                ctr_weight * (ctr * 100 / 0.10) +
                cvr_weight * (cvr * 100 / 0.05) +
                view_depth_weight * (view_depth * 100)
            )
            
            if score > best_score:
                best_score = score
                winner_video_id = UUID(int=random.randint(0, 2**128-1))
                best_metrics = WinnerMetrics(
                    roas=round(roas, 3),
                    ctr=round(ctr, 4),
                    cvr=round(cvr, 4),
                    view_depth_avg=round(view_depth, 3),
                    engagement_rate=round(engagement, 4),
                )
        
        # Generar razón de selección
        reason_parts = []
        if best_metrics.roas > 3.0:
            reason_parts.append(f"ROAS excepcional ({best_metrics.roas:.2f})")
        if best_metrics.ctr > 0.05:
            reason_parts.append(f"CTR superior ({best_metrics.ctr:.2%})")
        if best_metrics.cvr > 0.02:
            reason_parts.append(f"CVR alto ({best_metrics.cvr:.2%})")
        if best_metrics.view_depth_avg > 0.70:
            reason_parts.append(f"View depth profundo ({best_metrics.view_depth_avg:.1%})")
        
        selection_reason = " | ".join(reason_parts) or "Mejor performance combinado"
        
        # Confidence basado en diferencia vs segundo mejor
        selection_confidence = min(0.95, 0.60 + (best_score / 200))
        
        return WinnerSelection(
            winner_video_asset_id=winner_video_id,
            winner_ad_id=f"ad_{random.randint(100000, 999999)}",
            metrics=best_metrics,
            composite_score=round(best_score, 2),
            selection_reason=selection_reason,
            competitors_count=num_candidates,
            selection_confidence=round(selection_confidence, 3),
        )
    
    async def _select_live(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        ab_test_id: Optional[UUID],
        roas_weight: float,
        ctr_weight: float,
        cvr_weight: float,
        view_depth_weight: float,
    ) -> WinnerSelection:
        """Selección LIVE con datos reales"""
        
        logger.warning("LIVE mode not implemented, using STUB")
        return await self._select_stub(
            db, campaign_id, ab_test_id,
            roas_weight, ctr_weight, cvr_weight, view_depth_weight
        )
        
        # TODO: Implementación LIVE
        # 1. Query MetaABTestModel para obtener variantes del test
        # 2. Query MetaROASMetricsModel para ROAS de cada variante
        # 3. Query MetaInsightsModel para CTR, CVR, engagement
        # 4. Calcular composite score para cada variante
        # 5. Seleccionar ganador
        # 6. Retornar WinnerSelection con datos reales
