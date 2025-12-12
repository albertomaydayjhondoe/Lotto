"""
Budget Scaler para Meta Budget SPIKE Manager.
Aplica escalado de presupuestos según spikes detectados.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ledger import log_job_event
from app.meta_ads_client.client import MetaAdsClient
from app.meta_budget_spike.models import (
    BudgetScaleRequest,
    BudgetScaleResponse,
    MetaBudgetSpikeLogModel,
    ScaleAction,
    SpikeDetectionResult,
)

logger = logging.getLogger(__name__)


class BudgetScaler:
    """
    Aplica escalado de presupuestos de forma segura e idempotente.
    Integra con:
    - Meta Ads API Client
    - ROAS Engine
    - DB persistence
    """

    def __init__(self, db: Session):
        self.db = db
        self.meta_client = MetaAdsClient()
        # TODO: Integrate ROAS Engine for validation
        # self.roas_engine = ROASEngine(db)
        
        # Límites de seguridad
        self.min_budget = settings.AUTO_PUBLISHER_MIN_BUDGET_PER_VARIANT or 50.0
        self.max_budget = 10000.0
        self.max_scale_factor = 2.0  # Máximo 2x en un solo escalado

    async def scale_budget(
        self,
        request: BudgetScaleRequest,
        spike_result: SpikeDetectionResult | None = None,
    ) -> BudgetScaleResponse:
        """
        Escala presupuesto de un adset según la acción solicitada.
        
        Args:
            request: Request con adset_id y acción
            spike_result: Resultado de spike detection (opcional)
        
        Returns:
            Response con resultado del escalado
        """
        
        adset_id = request.adset_id
        action = request.action
        
        try:
            # 1. Obtener presupuesto actual
            current_budget = await self._get_current_budget(adset_id)
            
            if current_budget is None:
                return BudgetScaleResponse(
                    adset_id=adset_id,
                    old_budget=0.0,
                    new_budget=0.0,
                    action_applied=action,
                    success=False,
                    message=f"No se pudo obtener presupuesto actual para adset {adset_id}",
                )
            
            # 2. Calcular nuevo presupuesto
            new_budget = self._calculate_new_budget(current_budget, action)
            
            # 3. Aplicar límites de seguridad
            new_budget = self._apply_safety_limits(
                current_budget, new_budget, request.force
            )
            
            # 4. Aplicar cambio en Meta API
            if action == ScaleAction.PAUSE:
                success = await self._pause_adset(adset_id)
            else:
                success = await self._update_budget(adset_id, new_budget)
            
            # 5. Persistir en DB
            spike_log = self._create_spike_log(
                adset_id=adset_id,
                old_budget=current_budget,
                new_budget=new_budget,
                action=action,
                spike_result=spike_result,
                request=request,
                success=success,
            )
            
            # 6. Log del evento
            log_job_event(
                job_id=None,
                event_type="budget_scaled",
                message=f"Budget scaled: {adset_id} from ${current_budget} to ${new_budget}",
                metadata={
                    "adset_id": adset_id,
                    "old_budget": current_budget,
                    "new_budget": new_budget,
                    "action": action.value,
                    "success": success,
                },
            )
            
            message = (
                f"Presupuesto {'escalado' if success else 'NO escalado'}: "
                f"${current_budget:.2f} → ${new_budget:.2f} ({action.value})"
            )
            
            return BudgetScaleResponse(
                adset_id=adset_id,
                old_budget=current_budget,
                new_budget=new_budget if success else current_budget,
                action_applied=action,
                success=success,
                message=message,
                spike_log_id=spike_log.id if spike_log else None,
            )
        
        except Exception as e:
            error_msg = f"Error escalando presupuesto: {str(e)}"
            
            # Persistir error en DB
            self._create_spike_log(
                adset_id=adset_id,
                old_budget=0.0,
                new_budget=0.0,
                action=action,
                spike_result=spike_result,
                request=request,
                success=False,
                error_message=error_msg,
            )
            
            return BudgetScaleResponse(
                adset_id=adset_id,
                old_budget=0.0,
                new_budget=0.0,
                action_applied=action,
                success=False,
                message=error_msg,
            )

    def _calculate_new_budget(
        self, current_budget: float, action: ScaleAction
    ) -> float:
        """Calcula nuevo presupuesto según acción."""
        
        scale_factors = {
            ScaleAction.SCALE_UP_10: 1.10,
            ScaleAction.SCALE_UP_20: 1.20,
            ScaleAction.SCALE_UP_30: 1.30,
            ScaleAction.SCALE_UP_50: 1.50,
            ScaleAction.MAINTAIN: 1.00,
            ScaleAction.SCALE_DOWN_10: 0.90,
            ScaleAction.SCALE_DOWN_20: 0.80,
            ScaleAction.SCALE_DOWN_40: 0.60,
            ScaleAction.PAUSE: 0.00,
        }
        
        factor = scale_factors.get(action, 1.0)
        return current_budget * factor

    def _apply_safety_limits(
        self, current_budget: float, new_budget: float, force: bool
    ) -> float:
        """Aplica límites de seguridad al nuevo presupuesto."""
        
        if force:
            # En modo force, solo aplicar límites absolutos
            return max(self.min_budget, min(new_budget, self.max_budget))
        
        # Limitar cambio máximo
        max_change = current_budget * self.max_scale_factor
        min_change = current_budget / self.max_scale_factor
        
        new_budget = max(min_change, min(new_budget, max_change))
        
        # Limitar valores absolutos
        new_budget = max(self.min_budget, min(new_budget, self.max_budget))
        
        return new_budget

    async def _get_current_budget(self, adset_id: str) -> float | None:
        """Obtiene presupuesto actual del adset."""
        
        if settings.META_API_MODE == "stub":
            # STUB: Retornar presupuesto sintético
            import random
            return random.uniform(100, 1000)
        
        # LIVE: Consultar Meta API
        try:
            adset_data = await self.meta_client.get_adset(adset_id)
            return float(adset_data.get("daily_budget", 0)) / 100  # Convertir de centavos
        except Exception as e:
            logger.error(f"Error obteniendo presupuesto: {e}")
            return None

    async def _update_budget(self, adset_id: str, new_budget: float) -> bool:
        """Actualiza presupuesto en Meta API."""
        
        if settings.META_API_MODE == "stub":
            # STUB: Simular éxito
            return True
        
        # LIVE: Actualizar en Meta API
        try:
            budget_cents = int(new_budget * 100)
            await self.meta_client.update_adset(
                adset_id=adset_id,
                updates={"daily_budget": budget_cents},
            )
            return True
        except Exception as e:
            logger.error(f"Error actualizando presupuesto: {e}")
            return False

    async def _pause_adset(self, adset_id: str) -> bool:
        """Pausa un adset."""
        
        if settings.META_API_MODE == "stub":
            # STUB: Simular éxito
            return True
        
        # LIVE: Pausar en Meta API
        try:
            await self.meta_client.update_adset(
                adset_id=adset_id,
                updates={"status": "PAUSED"},
            )
            return True
        except Exception as e:
            logger.error(f"Error pausando adset: {e}")
            return False

    def _create_spike_log(
        self,
        adset_id: str,
        old_budget: float,
        new_budget: float,
        action: ScaleAction,
        spike_result: SpikeDetectionResult | None,
        request: BudgetScaleRequest,
        success: bool,
        error_message: str | None = None,
    ) -> MetaBudgetSpikeLogModel | None:
        """Crea registro en DB del spike y escalado aplicado."""
        
        try:
            log_entry = MetaBudgetSpikeLogModel(
                adset_id=adset_id,
                adset_name=spike_result.adset_name if spike_result else None,
                campaign_id=spike_result.campaign_id if spike_result else None,
                old_daily_budget=old_budget,
                new_daily_budget=new_budget,
                spike_type=spike_result.spike_type.value if spike_result and spike_result.spike_type else "manual",
                risk_level=spike_result.risk_level.value if spike_result else "low",
                reason=request.reason or (spike_result.reason if spike_result else "Manual scale"),
                metrics_snapshot=spike_result.current_metrics.dict() if spike_result else None,
                risk_score=spike_result.risk_score if spike_result else None,
                stability_score=spike_result.stability_score if spike_result else None,
                applied="applied" if success else "failed",
                error_message=error_message,
                created_at=datetime.utcnow(),
                applied_at=datetime.utcnow() if success else None,
            )
            
            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            
            return log_entry
        
        except Exception as e:
            logger.error(f"Error guardando spike log: {e}")
            self.db.rollback()
            return None

    async def scale_multiple(
        self,
        spike_results: list[SpikeDetectionResult],
        dry_run: bool = False,
    ) -> list[BudgetScaleResponse]:
        """
        Escala múltiples adsets basado en spikes detectados.
        
        Args:
            spike_results: Lista de resultados de spike detection
            dry_run: Si True, no aplica cambios (solo simula)
        
        Returns:
            Lista de respuestas de escalado
        """
        
        responses = []
        
        for spike_result in spike_results:
            if not spike_result.spike_detected:
                continue
            
            request = BudgetScaleRequest(
                adset_id=spike_result.adset_id,
                action=spike_result.recommended_action,
                reason=spike_result.reason,
            )
            
            if dry_run:
                # En dry_run, solo generar respuesta simulada
                responses.append(
                    BudgetScaleResponse(
                        adset_id=spike_result.adset_id,
                        old_budget=0.0,
                        new_budget=0.0,
                        action_applied=request.action,
                        success=False,
                        message="DRY RUN: No se aplicó cambio",
                    )
                )
            else:
                response = await self.scale_budget(request, spike_result)
                responses.append(response)
        
        return responses
