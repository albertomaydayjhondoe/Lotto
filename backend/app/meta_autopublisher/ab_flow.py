# backend/app/meta_autopublisher/ab_flow.py

"""
A/B Testing Flow Manager - Gestión de pruebas A/B y selección de ganadores.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
from statistics import mean, stdev

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.meta_insights_collector.collector import MetaInsightsCollector
from app.models.database import MetaAdInsightsModel

from .models import (
    CampaignVariant,
    ABTestConfig,
    WinnerSelection,
    VariantMetrics,
    WinnerSelectionCriteria
)

logger = get_logger(__name__)


class ABTestManager:
    """Gestiona A/B testing y selección de ganadores."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger
    
    async def launch_test(
        self,
        variants: List[CampaignVariant],
        config: ABTestConfig
    ) -> None:
        """Lanza el A/B test activando todas las variantes."""
        self.logger.info(f"[ABTest] Launching test with {len(variants)} variants")
        
        for variant in variants:
            if variant.campaign_id:
                # En stub mode, simulamos activación
                self.logger.info(f"[ABTest] Activated variant {variant.variant_id}")
    
    async def analyze_test_results(
        self,
        variants: List[CampaignVariant],
        config: ABTestConfig
    ) -> Dict:
        """Analiza resultados del A/B test."""
        self.logger.info(f"[ABTest] Analyzing results for {len(variants)} variants")
        
        results = {
            "total_variants": len(variants),
            "test_duration_hours": config.test_duration_hours,
            "embargo_hours": config.embargo_hours,
            "winner_criteria": config.winner_criteria,
            "variants_summary": []
        }
        
        for variant in variants:
            if variant.ad_id:
                metrics = await self._get_variant_metrics(variant.ad_id)
                results["variants_summary"].append({
                    "variant_id": variant.variant_id,
                    "variant_name": variant.variant_name,
                    "metrics": metrics
                })
        
        return results
    
    async def select_winner(
        self,
        variants: List[CampaignVariant],
        criteria: WinnerSelectionCriteria
    ) -> WinnerSelection:
        """Selecciona el ganador según criterio especificado."""
        self.logger.info(f"[ABTest] Selecting winner by {criteria}")
        
        # Obtener métricas de todas las variantes
        variant_metrics_list = []
        
        for variant in variants:
            if variant.ad_id:
                metrics = await self._get_variant_metrics(variant.ad_id)
                
                variant_metrics = VariantMetrics(
                    variant_id=variant.variant_id,
                    variant_name=variant.variant_name,
                    spend=metrics.get("spend", 0.0),
                    impressions=metrics.get("impressions", 0),
                    clicks=metrics.get("clicks", 0),
                    conversions=metrics.get("conversions", 0),
                    revenue=metrics.get("revenue", 0.0),
                    roas=metrics.get("roas", 0.0),
                    ctr=metrics.get("ctr", 0.0),
                    cpc=metrics.get("cpc", 0.0),
                    cpa=metrics.get("cpa", 0.0),
                    is_statistically_significant=True  # Simplificado para stub
                )
                
                variant_metrics_list.append(variant_metrics)
        
        if not variant_metrics_list:
            raise ValueError("No variants with metrics found")
        
        # Seleccionar ganador según criterio
        if criteria == WinnerSelectionCriteria.ROAS:
            winner_metrics = max(variant_metrics_list, key=lambda v: v.roas)
        elif criteria == WinnerSelectionCriteria.CPA:
            winner_metrics = min(variant_metrics_list, key=lambda v: v.cpa if v.cpa > 0 else float('inf'))
        elif criteria == WinnerSelectionCriteria.CTR:
            winner_metrics = max(variant_metrics_list, key=lambda v: v.ctr)
        elif criteria == WinnerSelectionCriteria.CONVERSIONS:
            winner_metrics = max(variant_metrics_list, key=lambda v: v.conversions)
        elif criteria == WinnerSelectionCriteria.REVENUE:
            winner_metrics = max(variant_metrics_list, key=lambda v: v.revenue)
        else:
            winner_metrics = max(variant_metrics_list, key=lambda v: v.roas)
        
        # Encontrar runner-up
        runner_up_metrics = None
        sorted_variants = sorted(
            variant_metrics_list,
            key=lambda v: getattr(v, criteria.value),
            reverse=criteria != WinnerSelectionCriteria.CPA
        )
        
        if len(sorted_variants) > 1:
            runner_up_metrics = sorted_variants[1]
        
        # Calcular mejora
        if runner_up_metrics:
            winner_value = getattr(winner_metrics, criteria.value)
            runner_up_value = getattr(runner_up_metrics, criteria.value)
            
            if runner_up_value > 0:
                improvement = ((winner_value - runner_up_value) / runner_up_value) * 100
            else:
                improvement = 100.0
        else:
            improvement = 100.0
        
        winner = WinnerSelection(
            winner_variant_id=winner_metrics.variant_id,
            winner_name=winner_metrics.variant_name,
            winner_metrics=winner_metrics,
            runner_up_variant_id=runner_up_metrics.variant_id if runner_up_metrics else None,
            runner_up_metrics=runner_up_metrics,
            improvement_percentage=improvement,
            confidence_level=0.95,  # Simplificado para stub
            selection_reason=f"Best {criteria.value}: {getattr(winner_metrics, criteria.value)}",
            all_variants=variant_metrics_list
        )
        
        self.logger.info(
            f"[ABTest] Winner selected: {winner.winner_name} "
            f"({criteria.value}={getattr(winner_metrics, criteria.value):.2f})"
        )
        
        return winner
    
    async def _get_variant_metrics(self, ad_id) -> Dict:
        """Obtiene métricas de una variante (stub mode genera datos sintéticos)."""
        # En stub mode, generamos métricas sintéticas
        spend = random.uniform(30, 100)
        impressions = random.randint(1000, 10000)
        clicks = int(impressions * random.uniform(0.01, 0.05))
        conversions = int(clicks * random.uniform(0.02, 0.10))
        revenue = conversions * random.uniform(10, 50)
        
        roas = revenue / spend if spend > 0 else 0.0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        cpc = spend / clicks if clicks > 0 else 0.0
        cpa = spend / conversions if conversions > 0 else 0.0
        
        return {
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "roas": roas,
            "ctr": ctr,
            "cpc": cpc,
            "cpa": cpa
        }
