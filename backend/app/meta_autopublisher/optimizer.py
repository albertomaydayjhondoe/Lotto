# backend/app/meta_autopublisher/optimizer.py

"""
Budget Optimizer - Integración con ROAS Engine para optimización de presupuestos.
"""
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.database import MetaCampaignModel
from app.meta_ads_orchestrator.roas_router import (
    calculate_roas,
    optimize_budget_allocation
)

logger = get_logger(__name__)


class BudgetOptimizer:
    """Optimiza presupuestos usando ROAS Engine."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger
    
    async def scale_budget(
        self,
        variant_id: str,
        scaling_factor: float,
        max_budget: Optional[float] = None
    ) -> Dict:
        """
        Escala el presupuesto de una variante ganadora.
        
        Args:
            variant_id: ID de la variante
            scaling_factor: Factor de escalado (ej: 2.0 = duplicar)
            max_budget: Presupuesto máximo permitido
            
        Returns:
            Dict con old_budget, new_budget, applied
        """
        # Extraer campaign_id del variant_id
        campaign_uuid = UUID(variant_id.split("_")[0])
        
        stmt = select(MetaCampaignModel).where(MetaCampaignModel.id == campaign_uuid)
        result = await self.db.execute(stmt)
        campaign = result.scalar()
        
        if not campaign:
            raise ValueError(f"Campaign not found for variant {variant_id}")
        
        old_budget = campaign.daily_budget or 0.0
        new_budget = old_budget * scaling_factor
        
        # Aplicar límite máximo si existe
        if max_budget and new_budget > max_budget:
            new_budget = max_budget
        
        # Actualizar presupuesto
        campaign.daily_budget = new_budget
        await self.db.commit()
        
        self.logger.info(
            f"[Optimizer] Scaled budget for {variant_id}: "
            f"${old_budget:.2f} -> ${new_budget:.2f} ({scaling_factor}x)"
        )
        
        return {
            "variant_id": variant_id,
            "old_budget": old_budget,
            "new_budget": new_budget,
            "scaling_factor": scaling_factor,
            "applied": True
        }
    
    async def optimize_allocation(
        self,
        campaign_ids: list,
        total_budget: float
    ) -> Dict:
        """
        Optimiza la asignación de presupuesto entre campañas según ROAS.
        
        Returns:
            Dict con allocations por campaña
        """
        # TODO: Integrar con ROAS Engine real
        # Por ahora, distribución uniforme en stub mode
        allocation_per_campaign = total_budget / len(campaign_ids) if campaign_ids else 0.0
        
        allocations = {
            str(campaign_id): allocation_per_campaign
            for campaign_id in campaign_ids
        }
        
        self.logger.info(f"[Optimizer] Budget allocated: {allocations}")
        
        return {
            "total_budget": total_budget,
            "allocations": allocations,
            "strategy": "uniform"  # En prod: "roas_weighted"
        }
